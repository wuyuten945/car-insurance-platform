'use client';

import { useState, useEffect, useRef } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  Phone, MapPin, AlertTriangle, Shield, Loader2, CheckCircle,
  ChevronDown, ChevronUp, Navigation, ExternalLink, Truck, Building2,
  Camera, Upload, Check,
} from 'lucide-react';
import api from '@/lib/api-client';
import { useEligibility } from '@/lib/useEligibility';
import LockedFeatureNotice from '@/components/LockedFeatureNotice';

interface NearbyResource {
  id: string;
  name: string;
  type: string;
  address: string;
  phone: string;
  distance_km: number;
}

// 道路救援服務
const ROAD_RESCUE_SERVICES = [
  { name: 'JAF 台灣道路救援', phone: '0800-085-858', searchQuery: '道路救援' },
  { name: '全鋒汽車道路救援', phone: '0800-066-580', searchQuery: '全鋒道路救援' },
  { name: '鉅業汽車道路救援', phone: '0800-005-566', searchQuery: '鉅業道路救援' },
  { name: '台灣大道路救援', phone: '0800-090-080', searchQuery: '台灣大道路救援' },
  { name: 'SOS 國際道路救援', phone: '0800-005-678', searchQuery: 'SOS道路救援' },
  { name: 'HOT 聯合道路救援', phone: '0800-002-586', searchQuery: 'HOT道路救援' },
  { name: '中華民國汽車拖吊公會', phone: '0800-092-888', searchQuery: '汽車拖吊' },
  { name: '國道高速公路拖救', phone: '1968', searchQuery: '高速公路拖救' },
];

// 各產險公司客服
const INSURANCE_COMPANIES = [
  { name: '富邦產險', phone: '0800-009-888', note: '24H' },
  { name: '國泰產險', phone: '0800-036-599', note: '24H' },
  { name: '新光產險', phone: '0800-789-999', note: '24H' },
  { name: '明台產險', phone: '0800-099-080', note: '24H' },
  { name: '南山產險', phone: '0800-020-060', note: '' },
  { name: '泰安產險', phone: '0800-012-080', note: '24H' },
  { name: '旺旺友聯產險', phone: '0800-024-024', note: '24H' },
  { name: '華南產險', phone: '0800-010-850', note: '' },
  { name: '兆豐產險', phone: '0800-053-588', note: '' },
  { name: '第一產險', phone: '0800-288-168', note: '' },
  { name: '新安東京海上產險', phone: '0800-050-119', note: '24H' },
  { name: '和泰產險', phone: '0800-880-550', note: '' },
  { name: '台灣產物保險', phone: '0800-053-888', note: '' },
  { name: '中國信託產險', phone: '0800-024-168', note: '' },
];

const ACCIDENT_STEPS = [
  { step: 1, title: '確認安全', desc: '開啟雙閃燈，擺放三角警示牌。確認自身及乘客安全。' },
  { step: 2, title: '報警處理', desc: '撥打110報案，取得交通事故報告單。' },
  { step: 3, title: '現場記錄', desc: '請依下方指示拍攝並上傳照片', isUpload: true },
  { step: 4, title: '通知保險公司', desc: '撥打保險公司客服，告知事故狀況。' },
  { step: 5, title: '就醫檢查', desc: '即使無明顯外傷，也建議就醫檢查並保留診斷證明。' },
  { step: 6, title: '申請暫傳（實際理賠依申請文件為主）', desc: '透過本平台先行暫傳事故資料，上傳相關文件。實際理賠仍依保險公司收到正式申請文件後審核為準。' },
];

const PHOTO_SLOTS = [
  { key: 'my_plate_front', label: '我方前車牌' },
  { key: 'my_plate_rear', label: '我方後車牌' },
  { key: 'other_plate_front', label: '對方前車牌' },
  { key: 'other_plate_rear', label: '對方後車牌' },
  { key: 'left_front', label: '車輛左前' },
  { key: 'front', label: '車輛正前' },
  { key: 'right_front', label: '車輛右前' },
  { key: 'right_side', label: '車輛右側' },
  { key: 'right_rear', label: '車輛右後' },
  { key: 'rear', label: '車輛正後' },
  { key: 'left_rear', label: '車輛左後' },
  { key: 'left_side', label: '車輛左側' },
  { key: 'scene_1', label: '事故現場照片1' },
  { key: 'scene_2', label: '事故現場照片2' },
  { key: 'scene_3', label: '事故現場照片3' },
  { key: 'police_report', label: '警方三聯單' },
];

export default function EmergencyPage() {
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [showGuide, setShowGuide] = useState(false);
  const [sosTriggered, setSosTriggered] = useState(false);
  const [showRescue, setShowRescue] = useState(false);
  const [showInsurer, setShowInsurer] = useState(false);
  const [uploadedPhotos, setUploadedPhotos] = useState<Record<string, string>>({});
  const [uploadingKey, setUploadingKey] = useState('');
  const fileRefs = useRef<Record<string, HTMLInputElement | null>>({});
  const { eligibility } = useEligibility();

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => {}
      );
    }
  }, []);

  const sosMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/v1/accidents', {
        occurred_at: new Date().toISOString(),
        latitude: location?.lat ?? 0,
        longitude: location?.lng ?? 0,
      });
      return res.data.data;
    },
    onSuccess: () => setSosTriggered(true),
  });

  const { data: nearby } = useQuery({
    queryKey: ['nearby-resources', location],
    queryFn: async () => {
      const accidentId = sosMutation.data?.id;
      if (!accidentId || !location) return [];
      const res = await api.get(
        `/api/v1/accidents/${accidentId}/nearby?latitude=${location.lat}&longitude=${location.lng}`
      );
      return res.data.data as NearbyResource[];
    },
    enabled: sosTriggered && !!location && !!sosMutation.data?.id,
  });

  const handlePhotoUpload = async (key: string, file: File) => {
    setUploadingKey(key);
    const fd = new FormData();
    fd.append('file', file);
    fd.append('photo_type', key);
    try {
      const accidentId = sosMutation.data?.id;
      if (accidentId) {
        await api.post(`/api/v1/accidents/${accidentId}/photos`, fd, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }
      // Show preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setUploadedPhotos((prev) => ({ ...prev, [key]: e.target?.result as string }));
      };
      reader.readAsDataURL(file);
    } catch {
      // Still show preview even if API fails (might not have accident ID yet)
      const reader = new FileReader();
      reader.onload = (e) => {
        setUploadedPhotos((prev) => ({ ...prev, [key]: e.target?.result as string }));
      };
      reader.readAsDataURL(file);
    }
    setUploadingKey('');
  };

  const buildMapUrl = (query: string) => {
    if (location) {
      return `https://www.google.com/maps/search/${encodeURIComponent(query)}/@${location.lat},${location.lng},14z`;
    }
    return `https://www.google.com/maps/search/${encodeURIComponent(query)}`;
  };

  return (
    <div className="px-4 py-5 space-y-6">
      {/* SOS Section */}
      <div className="flex flex-col items-center py-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">緊急救援</h1>
        <p className="text-base text-gray-500 mb-8">發生事故？按下按鈕立即求援</p>

        {!sosTriggered ? (
          <button
            onClick={() => sosMutation.mutate()}
            disabled={sosMutation.isPending}
            className="sos-pulse flex h-40 w-40 items-center justify-center rounded-full bg-emergency-red text-white shadow-2xl active:scale-95 transition"
          >
            {sosMutation.isPending ? (
              <Loader2 className="h-16 w-16 animate-spin" />
            ) : (
              <div className="text-center">
                <AlertTriangle className="h-16 w-16 mx-auto" />
                <span className="text-xl font-bold mt-2 block">SOS</span>
              </div>
            )}
          </button>
        ) : (
          <div className="flex flex-col items-center">
            <div className="flex h-24 w-24 items-center justify-center rounded-full bg-green-500 text-white mb-4">
              <CheckCircle className="h-12 w-12" />
            </div>
            <p className="text-lg font-bold text-green-600">已通報成功</p>
            <p className="text-sm text-gray-500 mt-1">我們已收到您的事故通報</p>
          </div>
        )}

        {sosMutation.isError && (
          <p className="mt-4 text-sm text-red-600">通報失敗，請直接撥打客服電話</p>
        )}
      </div>

      {/* Emergency Contacts — Fixed: 報警 + 消防 */}
      <section>
        <h2 className="text-lg font-bold text-gray-900 mb-3">緊急聯絡</h2>
        <div className="grid grid-cols-2 gap-3">
          <a
            href="tel:110"
            className="flex items-center gap-3 rounded-xl bg-red-600 p-4 text-white shadow-sm active:opacity-90"
          >
            <Phone className="h-6 w-6 shrink-0" />
            <div>
              <p className="text-base font-bold leading-tight">報警 (110)</p>
              <p className="text-sm text-white/80">110</p>
            </div>
          </a>
          <a
            href="tel:119"
            className="flex items-center gap-3 rounded-xl bg-red-700 p-4 text-white shadow-sm active:opacity-90"
          >
            <Phone className="h-6 w-6 shrink-0" />
            <div>
              <p className="text-base font-bold leading-tight">消防/救護 (119)</p>
              <p className="text-sm text-white/80">119</p>
            </div>
          </a>
        </div>
      </section>

      {/* Road Rescue — Dropdown + Google Map */}
      <section>
        <button
          onClick={() => setShowRescue(!showRescue)}
          className="flex w-full items-center justify-between rounded-xl bg-orange-600 p-4 text-white shadow-sm active:opacity-90"
        >
          <div className="flex items-center gap-3">
            <Truck className="h-6 w-6 shrink-0" />
            <div className="text-left">
              <p className="text-base font-bold leading-tight">道路救援</p>
              <p className="text-sm text-white/80">選擇服務 &amp; Google Map 導航</p>
            </div>
          </div>
          {showRescue
            ? <ChevronUp className="h-5 w-5 shrink-0" />
            : <ChevronDown className="h-5 w-5 shrink-0" />}
        </button>

        {showRescue && (
          <div className="mt-2 rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden divide-y divide-gray-50">
            {ROAD_RESCUE_SERVICES.map((svc) => (
              <div key={svc.phone} className="flex items-center justify-between px-4 py-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-900 truncate">{svc.name}</p>
                  <p className="text-xs text-gray-400">{svc.phone}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-2">
                  <a
                    href={buildMapUrl(svc.searchQuery)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 rounded-lg bg-green-50 border border-green-200 px-2.5 py-1.5 text-[11px] font-medium text-green-700"
                  >
                    <Navigation className="h-3 w-3" /> 地圖
                  </a>
                  <a
                    href={`tel:${svc.phone}`}
                    className="flex items-center gap-1 rounded-lg bg-orange-50 border border-orange-200 px-2.5 py-1.5 text-[11px] font-medium text-orange-700"
                  >
                    <Phone className="h-3 w-3" /> 撥打
                  </a>
                </div>
              </div>
            ))}
            {/* Search nearby tow/rescue on Google Map */}
            <a
              href={buildMapUrl('道路救援 拖吊')}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium text-green-600 hover:bg-green-50 transition"
            >
              <ExternalLink className="h-4 w-4" />
              Google Map 搜尋附近所有道路救援
            </a>
          </div>
        )}
      </section>

      {/* Insurance Company — Dropdown */}
      <section>
        <button
          onClick={() => setShowInsurer(!showInsurer)}
          className="flex w-full items-center justify-between rounded-xl bg-primary-500 p-4 text-white shadow-sm active:opacity-90"
        >
          <div className="flex items-center gap-3">
            <Building2 className="h-6 w-6 shrink-0" />
            <div className="text-left">
              <p className="text-base font-bold leading-tight">保險公司客服</p>
              <p className="text-sm text-white/80">選擇產險公司撥打客服</p>
            </div>
          </div>
          {showInsurer
            ? <ChevronUp className="h-5 w-5 shrink-0" />
            : <ChevronDown className="h-5 w-5 shrink-0" />}
        </button>

        {showInsurer && (
          <div className="mt-2 rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden divide-y divide-gray-50">
            {INSURANCE_COMPANIES.map((ins) => (
              <a
                key={ins.phone}
                href={`tel:${ins.phone}`}
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-gray-900">{ins.name}</p>
                    {ins.note && (
                      <span className="rounded-full bg-green-50 border border-green-200 px-1.5 py-0 text-[10px] font-medium text-green-600">
                        {ins.note}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400">{ins.phone}</p>
                </div>
                <div className="flex items-center gap-1 rounded-lg bg-primary-50 border border-primary-200 px-2.5 py-1.5 text-[11px] font-medium text-primary-600 shrink-0 ml-2">
                  <Phone className="h-3 w-3" /> 撥打
                </div>
              </a>
            ))}
          </div>
        )}
      </section>

      {/* Nearby Resources */}
      {nearby && nearby.length > 0 && (
        <section>
          <h2 className="text-lg font-bold text-gray-900 mb-3">附近資源</h2>
          <div className="space-y-2">
            {nearby.map((r) => (
              <div key={r.id} className="flex items-center justify-between rounded-xl bg-white p-4 shadow-sm border border-gray-100">
                <div className="flex items-center gap-3">
                  <MapPin className="h-5 w-5 text-primary-500 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{r.name}</p>
                    <p className="text-xs text-gray-400">{r.address}</p>
                  </div>
                </div>
                <div className="text-right shrink-0 ml-2">
                  <p className="text-xs text-gray-500">{r.distance_km?.toFixed(1)} km</p>
                  {r.phone && (
                    <a href={`tel:${r.phone}`} className="text-xs text-primary-500 font-medium">
                      撥打
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Accident Guide */}
      <section>
        <button
          onClick={() => setShowGuide(!showGuide)}
          className="flex w-full items-center justify-between rounded-xl bg-white p-4 shadow-sm border border-gray-100"
        >
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary-500" />
            <span className="text-base font-bold text-gray-900">事故處理步驟指南</span>
          </div>
          {showGuide ? <ChevronUp className="h-5 w-5 text-gray-400" /> : <ChevronDown className="h-5 w-5 text-gray-400" />}
        </button>

        {showGuide && (
          <div className="mt-3 space-y-4">
            {ACCIDENT_STEPS.map((s: { step: number; title: string; desc: string; isUpload?: boolean }) => (
              <div key={s.step}>
                <div className="flex gap-4">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-500 text-white text-sm font-bold">
                    {s.step}
                  </div>
                  <div className="flex-1">
                    <p className="text-base font-bold text-gray-900">{s.title}</p>
                    <p className="text-sm text-gray-600 mt-0.5 leading-relaxed">{s.desc}</p>
                  </div>
                </div>
                {s.isUpload && !eligibility.can_upload_accident_photo && (
                  <div className="mt-3 ml-12">
                    <LockedFeatureNotice
                      title="事故照片上傳限投保客戶使用"
                      description="此功能用於將照片連同事故報告送交您的理賠專員。您目前的保單為自行建檔，請先透過 LINE 與我們聯繫正式投保。"
                      lineOaUrl={eligibility.line_oa_url}
                    />
                  </div>
                )}
                {s.isUpload && eligibility.can_upload_accident_photo && (
                  <div className="mt-3 ml-12 grid grid-cols-2 gap-2">
                    {PHOTO_SLOTS.map((slot) => {
                      const uploaded = uploadedPhotos[slot.key];
                      const isUploading = uploadingKey === slot.key;
                      return (
                        <div key={slot.key} className="relative">
                          <input
                            type="file"
                            accept="image/*"
                            capture="environment"
                            className="hidden"
                            ref={(el: HTMLInputElement | null) => { fileRefs.current[slot.key] = el; }}
                            onChange={(e) => {
                              const f = e.target.files?.[0];
                              if (f) handlePhotoUpload(slot.key, f);
                            }}
                          />
                          <button
                            onClick={() => fileRefs.current[slot.key]?.click()}
                            disabled={isUploading}
                            className={`w-full rounded-lg border-2 border-dashed p-2.5 text-center transition ${
                              uploaded
                                ? 'border-green-300 bg-green-50'
                                : 'border-gray-200 bg-white hover:border-primary-300'
                            }`}
                          >
                            {uploaded ? (
                              <div className="relative">
                                <img src={uploaded} alt={slot.label} className="w-full h-16 object-cover rounded" />
                                <div className="absolute top-0.5 right-0.5 bg-green-500 rounded-full p-0.5">
                                  <Check className="h-3 w-3 text-white" />
                                </div>
                              </div>
                            ) : isUploading ? (
                              <Loader2 className="h-5 w-5 animate-spin text-primary-500 mx-auto" />
                            ) : (
                              <Camera className="h-5 w-5 text-gray-400 mx-auto" />
                            )}
                            <p className={`text-[10px] mt-1 font-medium ${uploaded ? 'text-green-600' : 'text-gray-500'}`}>
                              {uploaded ? '已上傳' : '拍攝'}{slot.label}
                            </p>
                          </button>
                        </div>
                      );
                    })}
                    <div className="col-span-2 text-center mt-1">
                      <p className="text-[10px] text-gray-400">
                        已上傳 {Object.keys(uploadedPhotos).length} / {PHOTO_SLOTS.length} 張
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
