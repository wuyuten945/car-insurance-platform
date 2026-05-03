'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Car, ChevronLeft, Upload, Camera, AlertTriangle, CheckCircle,
  Clock, XCircle, Shield, Loader2, Calendar, FileText,
} from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';

interface Vehicle {
  id: string;
  plate_number: string;
  brand: string | null;
  model: string | null;
  year: number | null;
  color: string | null;
  engine_cc: number | null;
  is_primary: boolean;
  registration_image_url: string | null;
  registration_date: string | null;
  registration_expiry: string | null;
  last_inspection_date: string | null;
}

interface InspectionStatus {
  vehicle_id: string;
  plate_number: string;
  brand: string | null;
  model: string | null;
  registration_expiry: string | null;
  days_to_inspection: number | null;
  inspection_status: string;
  has_compulsory_insurance: boolean;
  compulsory_expiry: string | null;
  can_inspect: boolean;
  warnings: string[];
  registration_image_url: string | null;
  last_inspection_date: string | null;
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; icon: typeof CheckCircle }> = {
  ok: { label: '正常', color: 'text-green-600', bg: 'bg-green-50 border-green-200', icon: CheckCircle },
  upcoming: { label: '即將到期', color: 'text-yellow-600', bg: 'bg-yellow-50 border-yellow-200', icon: Clock },
  urgent: { label: '緊急', color: 'text-red-600', bg: 'bg-red-50 border-red-200', icon: AlertTriangle },
  overdue: { label: '已逾期', color: 'text-red-700', bg: 'bg-red-100 border-red-300', icon: XCircle },
  unknown: { label: '未設定', color: 'text-gray-500', bg: 'bg-gray-50 border-gray-200', icon: Clock },
};

export default function VehiclesPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) router.replace('/login');
  }, [isAuthenticated, router]);

  const { data: vehicles, isLoading } = useQuery({
    queryKey: ['vehicles'],
    queryFn: async () => {
      const res = await api.get('/api/v1/customers/vehicles');
      return res.data.data as Vehicle[];
    },
    enabled: isAuthenticated,
  });

  if (!isAuthenticated) return null;

  return (
    <div className="px-4 py-5 space-y-4">
      <div className="flex items-center gap-3">
        <Link href="/profile" className="p-1">
          <ChevronLeft className="h-5 w-5 text-gray-600" />
        </Link>
        <h1 className="text-lg font-bold text-gray-900">我的車輛</h1>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      ) : !vehicles?.length ? (
        <div className="text-center py-12">
          <Car className="h-12 w-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-400">尚無車輛資料</p>
        </div>
      ) : (
        vehicles.map((v) => <VehicleCard key={v.id} vehicle={v} />)
      )}
    </div>
  );
}

function VehicleCard({ vehicle }: { vehicle: Vehicle }) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showStatus, setShowStatus] = useState(false);

  const { data: inspectionStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['inspection-status', vehicle.id],
    queryFn: async () => {
      const res = await api.get(`/api/v1/customers/vehicles/${vehicle.id}/inspection-status`);
      return res.data.data as InspectionStatus;
    },
    enabled: showStatus,
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post(`/api/v1/customers/vehicles/${vehicle.id}/registration`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
  };

  const statusConfig = inspectionStatus
    ? STATUS_CONFIG[inspectionStatus.inspection_status] || STATUS_CONFIG.unknown
    : null;

  // 品牌對應的車輛圖（目前只有 BMW i3，其他品牌 fall back 到 icon）
  const brandImage =
    vehicle.brand === 'BMW' && vehicle.model === 'i3' ? '/bmw-i3.jpg' : null;

  return (
    <div className="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
      {/* Vehicle hero image (有對應品牌圖時顯示) */}
      {brandImage && (
        <div className="relative w-full h-40 bg-gray-900">
          <img
            src={brandImage}
            alt={`${vehicle.brand} ${vehicle.model}`}
            className="w-full h-full object-cover"
          />
          <div className="absolute bottom-2 left-3 text-white">
            <p className="text-[11px] opacity-80 font-medium tracking-wide">
              {vehicle.brand} {vehicle.model} {vehicle.year}
            </p>
          </div>
        </div>
      )}

      {/* Vehicle info header */}
      <div className="p-4">
        <div className="flex items-center gap-3 mb-3">
          {!brandImage && (
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-50">
              <Car className="h-6 w-6 text-primary-500" />
            </div>
          )}
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-gray-900">{vehicle.plate_number}</h3>
              {vehicle.is_primary && (
                <span className="rounded-full bg-primary-50 px-2 py-0.5 text-[10px] font-medium text-primary-500">
                  主要
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500">
              {[vehicle.brand, vehicle.model, vehicle.year ? `${vehicle.year}年` : null]
                .filter(Boolean)
                .join(' ')}
              {vehicle.color ? ` | ${vehicle.color}` : ''}
            </p>
          </div>
        </div>

        {/* Registration info */}
        <div className="grid grid-cols-2 gap-2 text-xs mb-3">
          <div className="rounded-lg bg-gray-50 p-2.5">
            <p className="text-gray-400 mb-0.5">行照到期</p>
            <p className="font-semibold text-gray-700">
              {vehicle.registration_expiry || '未設定'}
            </p>
          </div>
          <div className="rounded-lg bg-gray-50 p-2.5">
            <p className="text-gray-400 mb-0.5">上次驗車</p>
            <p className="font-semibold text-gray-700">
              {vehicle.last_inspection_date || '無紀錄'}
            </p>
          </div>
        </div>

        {/* Registration image */}
        {vehicle.registration_image_url ? (
          <div className="mb-3">
            <p className="text-xs text-gray-400 mb-1.5">行照圖片</p>
            <div className="relative rounded-lg overflow-hidden border border-gray-200">
              <img
                src={`http://localhost:8000${vehicle.registration_image_url}`}
                alt="行照"
                className="w-full h-40 object-cover"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="absolute bottom-2 right-2 flex items-center gap-1 rounded-lg bg-white/90 px-2.5 py-1.5 text-xs font-medium text-gray-700 shadow-sm"
              >
                <Camera className="h-3.5 w-3.5" /> 重新上傳
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadMutation.isPending}
            className="w-full mb-3 flex items-center justify-center gap-2 rounded-xl border-2 border-dashed border-gray-200 py-6 text-sm text-gray-400 hover:border-primary-300 hover:text-primary-500 transition"
          >
            {uploadMutation.isPending ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Upload className="h-5 w-5" />
            )}
            {uploadMutation.isPending ? '上傳中...' : '上傳行照圖片'}
          </button>
        )}

        {uploadMutation.isSuccess && (
          <div className="mb-3 rounded-lg bg-green-50 p-2.5 text-xs text-green-600">
            行照已上傳成功
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,application/pdf,.pdf"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>

      {/* Inspection status toggle */}
      <div className="border-t border-gray-100">
        <button
          onClick={() => setShowStatus(!showStatus)}
          className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-primary-500 hover:bg-gray-50 transition"
        >
          <span className="flex items-center gap-1.5">
            <Shield className="h-4 w-4" />
            驗車狀態檢查
          </span>
          <span className="text-xs text-gray-400">{showStatus ? '收起' : '展開'}</span>
        </button>

        {showStatus && (
          <div className="px-4 pb-4 space-y-3">
            {statusLoading ? (
              <div className="flex justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-primary-500" />
              </div>
            ) : inspectionStatus && statusConfig ? (
              <>
                {/* Status badge */}
                <div className={`flex items-center gap-2 rounded-lg border p-3 ${statusConfig.bg}`}>
                  <statusConfig.icon className={`h-5 w-5 ${statusConfig.color}`} />
                  <div>
                    <p className={`text-sm font-semibold ${statusConfig.color}`}>
                      驗車狀態：{statusConfig.label}
                    </p>
                    {inspectionStatus.days_to_inspection != null && (
                      <p className="text-xs text-gray-500 mt-0.5">
                        {inspectionStatus.days_to_inspection > 0
                          ? `距離到期還有 ${inspectionStatus.days_to_inspection} 天`
                          : `已逾期 ${Math.abs(inspectionStatus.days_to_inspection)} 天`}
                      </p>
                    )}
                  </div>
                </div>

                {/* Compulsory insurance status */}
                <div className={`flex items-center gap-2 rounded-lg border p-3 ${
                  inspectionStatus.has_compulsory_insurance
                    ? 'bg-green-50 border-green-200'
                    : 'bg-red-50 border-red-200'
                }`}>
                  {inspectionStatus.has_compulsory_insurance ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-600" />
                  )}
                  <div>
                    <p className={`text-sm font-semibold ${
                      inspectionStatus.has_compulsory_insurance ? 'text-green-600' : 'text-red-600'
                    }`}>
                      強制險：{inspectionStatus.has_compulsory_insurance ? '有效' : '無效 / 未投保'}
                    </p>
                    {inspectionStatus.compulsory_expiry && (
                      <p className="text-xs text-gray-500 mt-0.5">
                        到期日：{inspectionStatus.compulsory_expiry}
                      </p>
                    )}
                  </div>
                </div>

                {/* Can inspect? */}
                <div className={`rounded-lg border p-3 ${
                  inspectionStatus.can_inspect
                    ? 'bg-green-50 border-green-200'
                    : 'bg-red-50 border-red-200'
                }`}>
                  <p className={`text-sm font-semibold ${
                    inspectionStatus.can_inspect ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {inspectionStatus.can_inspect ? '可辦理驗車' : '無法辦理驗車'}
                  </p>
                </div>

                {/* Warnings */}
                {inspectionStatus.warnings.length > 0 && (
                  <div className="space-y-2">
                    {inspectionStatus.warnings.map((w, i) => (
                      <div key={i} className="flex items-start gap-2 rounded-lg bg-yellow-50 border border-yellow-200 p-3">
                        <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5 shrink-0" />
                        <p className="text-xs text-yellow-700">{w}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Link to inspection stations */}
                <Link
                  href="/inspection"
                  className="flex items-center justify-center gap-2 rounded-xl bg-primary-500 py-3 text-sm font-semibold text-white hover:bg-primary-700 transition"
                >
                  <FileText className="h-4 w-4" />
                  查詢附近驗車廠
                </Link>
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
