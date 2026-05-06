'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Car, ChevronLeft, Upload, Camera, AlertTriangle, CheckCircle,
  Clock, XCircle, Shield, Loader2, FileText, Plus, Pencil, Trash2,
} from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import { useT } from '@/lib/i18n/LanguageProvider';
import { useAuthGuard } from '@/lib/useAuthGuard';
import { useIdleLogout } from '@/lib/useIdleLogout';
import VehicleFormModal, { type VehiclePayload } from '@/components/VehicleFormModal';
import AddToCalendar from '@/components/AddToCalendar';
import InspectionInsuranceGuide from '@/components/InspectionInsuranceGuide';
import { useEligibility } from '@/lib/useEligibility';

interface Vehicle {
  id: string;
  plate_number: string;
  brand: string | null;
  model: string | null;
  year: number | null;
  manufacture_month?: number | null;
  color: string | null;
  vin?: string | null;
  engine_cc: number | null;
  vehicle_type?: string | null;
  fuel_type?: string | null;
  is_primary: boolean;
  registration_image_url: string | null;
  registration_date: string | null;
  reissue_date?: string | null;
  registration_expiry: string | null;
  last_inspection_date: string | null;
  data_source?: string;  // 'agent' | 'self'
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
  const { ready: __authReady } = useAuthGuard();
  useIdleLogout();
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { t } = useT();

  useEffect(() => {
    if (!isAuthenticated) router.replace('/login');
  }, [isAuthenticated, router]);

  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<VehiclePayload | null>(null);
  const { eligibility } = useEligibility();

  const { data: vehicles, isLoading } = useQuery({
    queryKey: ['vehicles'],
    queryFn: async () => {
      const res = await api.get('/api/v1/customers/vehicles');
      return res.data.data as Vehicle[];
    },
    enabled: isAuthenticated,
  });

  // 抓自己所有保單，給驗車卡片用來檢查強制險夠不夠
  const { data: allPolicies } = useQuery({
    queryKey: ['my-policies-for-inspection'],
    queryFn: async () => {
      const res = await api.get('/api/v1/policies');
      return (res.data.data || []) as Array<{
        id: string; status: string; vehicle_id?: string | null;
        compulsory_end_date?: string | null; end_date?: string;
        data_source?: string;
      }>;
    },
    enabled: isAuthenticated,
  });

  const handleAdd = () => { setEditing(null); setModalOpen(true); };
  const handleEdit = (v: Vehicle) => {
    setEditing({
      id: v.id, plate_number: v.plate_number,
      brand: v.brand, model: v.model, year: v.year,
      manufacture_month: v.manufacture_month ?? null,
      color: v.color, vin: v.vin ?? null, engine_cc: v.engine_cc,
      vehicle_type: v.vehicle_type ?? null, fuel_type: v.fuel_type ?? null,
      registration_date: v.registration_date,
      reissue_date: v.reissue_date ?? null,
      registration_expiry: v.registration_expiry,
    });
    setModalOpen(true);
  };
  const handleSaved = () => {
    queryClient.invalidateQueries({ queryKey: ['vehicles'] });
    queryClient.invalidateQueries({ queryKey: ['eligibility'] });
  };

  if (!isAuthenticated) return null;

  if (!__authReady) return null;

  return (
    <div className="px-4 py-5 space-y-4">
      <div className="flex items-center gap-3">
        <Link href="/profile" className="p-1">
          <ChevronLeft className="h-5 w-5 text-gray-600" />
        </Link>
        <h1 className="text-lg font-bold text-gray-900 flex-1">{t('vehicles.title')}</h1>
        <button onClick={handleAdd} className="flex items-center gap-1 rounded-lg bg-primary-500 px-3 py-2 text-xs font-semibold text-white hover:bg-primary-700">
          <Plus className="h-4 w-4" /> 新增車輛
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      ) : !vehicles?.length ? (
        <div className="text-center py-12">
          <Car className="h-12 w-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-400">{t('vehicles.empty')}</p>
          <button onClick={handleAdd} className="mt-4 inline-flex items-center gap-1 rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white">
            <Plus className="h-4 w-4" /> 新增第一輛車
          </button>
        </div>
      ) : (
        vehicles.map((v) => (
          <VehicleCard
            key={v.id}
            vehicle={v}
            onEdit={() => handleEdit(v)}
            policies={(allPolicies ?? []).filter((p) => p.vehicle_id === v.id)}
            hasAgentPolicy={eligibility.has_agent_policy}
            lineOaUrl={eligibility.line_oa_url}
          />
        ))
      )}

      <VehicleFormModal
        open={modalOpen}
        initial={editing}
        onClose={() => setModalOpen(false)}
        onSaved={handleSaved}
      />
    </div>
  );
}

interface PolicyForGuide {
  id: string; status: string; vehicle_id?: string | null;
  compulsory_end_date?: string | null; end_date?: string;
  data_source?: string;
}
function VehicleCard({
  vehicle, onEdit, policies, hasAgentPolicy, lineOaUrl,
}: {
  vehicle: Vehicle; onEdit: () => void;
  policies: PolicyForGuide[]; hasAgentPolicy: boolean; lineOaUrl: string;
}) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showStatus, setShowStatus] = useState(false);
  const { t } = useT();
  const isSelf = (vehicle.data_source || 'agent') === 'self';

  const deleteMutation = useMutation({
    mutationFn: async () => {
      await api.delete(`/api/v1/customers/vehicles/${vehicle.id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
    },
  });

  const handleDelete = () => {
    if (!confirm(`確定要刪除車輛「${vehicle.plate_number}」嗎？此動作無法復原。`)) return;
    deleteMutation.mutate();
  };

  const STATUS_LABEL: Record<string, string> = {
    ok: t('vehicles.statusOk'),
    upcoming: t('vehicles.statusUpcoming'),
    urgent: t('vehicles.statusUrgent'),
    overdue: t('vehicles.statusOverdue'),
    unknown: t('vehicles.statusUnknown'),
  };

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
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-bold text-gray-900">{vehicle.plate_number}</h3>
              {vehicle.is_primary && (
                <span className="rounded-full bg-primary-50 px-2 py-0.5 text-[10px] font-medium text-primary-500">
                  {t('vehicles.primary')}
                </span>
              )}
              {isSelf ? (
                <span className="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-medium text-blue-700">👤 自填</span>
              ) : (
                <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700">🛡 業務員建檔</span>
              )}
            </div>
            <p className="text-xs text-gray-500">
              {[vehicle.brand, vehicle.model, vehicle.year ? `${vehicle.year}${t('common.year')}` : null]
                .filter(Boolean)
                .join(' ')}
              {vehicle.color ? ` | ${vehicle.color}` : ''}
            </p>
          </div>
        </div>

        {/* Registration info */}
        <div className="grid grid-cols-2 gap-2 text-xs mb-3">
          <div className="rounded-lg bg-gray-50 p-2.5">
            <div className="flex items-center justify-between mb-0.5 gap-1">
              <p className="text-gray-400">{t('vehicles.regExpiry')}</p>
              {vehicle.registration_expiry && (
                <AddToCalendar
                  title={`驗車到期 — ${vehicle.plate_number}`}
                  date={vehicle.registration_expiry}
                  description={`車牌：${vehicle.plate_number}\n品牌車型：${vehicle.brand || ''} ${vehicle.model || ''}\n（提醒：到期前 30 天 ~ 後 30 天可驗車）`}
                />
              )}
            </div>
            <p className="font-semibold text-gray-700">
              {vehicle.registration_expiry || t('vehicles.notSet')}
            </p>
          </div>
          <div className="rounded-lg bg-gray-50 p-2.5">
            <p className="text-gray-400 mb-0.5">{t('vehicles.lastInspect')}</p>
            <p className="font-semibold text-gray-700">
              {vehicle.last_inspection_date || t('vehicles.noRecord')}
            </p>
          </div>
        </div>

        {/* 驗車期間 + 強制險引導 */}
        <InspectionInsuranceGuide
          vehicleId={vehicle.id}
          vehiclePlate={vehicle.plate_number}
          registrationExpiry={vehicle.registration_expiry}
          policies={policies}
          hasAgentPolicy={hasAgentPolicy}
          lineOaUrl={lineOaUrl}
        />

        {/* Registration image — 只有自填紀錄能上傳/更換；業務員建檔的只讀 */}
        {vehicle.registration_image_url ? (
          <div className="mb-3">
            <p className="text-xs text-gray-400 mb-1.5">{t('vehicles.regImage')}</p>
            <div className="relative rounded-lg overflow-hidden border border-gray-200">
              <img
                src={`${process.env.NEXT_PUBLIC_API_URL || ''}${vehicle.registration_image_url}`}
                alt={t('vehicles.regImageAlt')}
                className="w-full h-40 object-cover"
              />
              {isSelf && (
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="absolute bottom-2 right-2 flex items-center gap-1 rounded-lg bg-white/90 px-2.5 py-1.5 text-xs font-medium text-gray-700 shadow-sm"
                >
                  <Camera className="h-3.5 w-3.5" /> {t('vehicles.reupload')}
                </button>
              )}
            </div>
          </div>
        ) : isSelf ? (
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
            {uploadMutation.isPending ? t('vehicles.uploading') : t('vehicles.uploadRegImage')}
          </button>
        ) : (
          <div className="mb-3 rounded-lg bg-gray-50 p-3 text-xs text-gray-500 text-center">
            尚未上傳行照（如需更新請聯繫業務員）
          </div>
        )}

        {uploadMutation.isSuccess && (
          <div className="mb-3 rounded-lg bg-green-50 p-2.5 text-xs text-green-600">
            {t('vehicles.uploadOk')}
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,application/pdf,.pdf"
          className="hidden"
          onChange={handleFileChange}
        />

        {/* 自填紀錄 → 編輯 / 刪除按鈕；業務員建檔的紀錄唯讀 */}
        {isSelf ? (
          <div className="flex gap-2 pt-2 border-t border-gray-100 mt-2">
            <button onClick={onEdit} className="flex-1 flex items-center justify-center gap-1 rounded-lg bg-gray-100 hover:bg-gray-200 px-3 py-2 text-xs font-semibold text-gray-700">
              <Pencil className="h-3.5 w-3.5" /> 編輯
            </button>
            <button onClick={handleDelete} disabled={deleteMutation.isPending} className="flex items-center justify-center gap-1 rounded-lg bg-red-50 hover:bg-red-100 px-3 py-2 text-xs font-semibold text-red-600 disabled:opacity-50">
              {deleteMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
              刪除
            </button>
          </div>
        ) : (
          <p className="text-[11px] text-gray-400 mt-2 pt-2 border-t border-gray-100">
            此車輛由業務員 / 平台建檔，如需修改請聯繫您的業務員。
          </p>
        )}
      </div>

      {/* Inspection status toggle */}
      <div className="border-t border-gray-100">
        <button
          onClick={() => setShowStatus(!showStatus)}
          className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-primary-500 hover:bg-gray-50 transition"
        >
          <span className="flex items-center gap-1.5">
            <Shield className="h-4 w-4" />
            {t('vehicles.statusCheck')}
          </span>
          <span className="text-xs text-gray-400">{showStatus ? t('vehicles.collapse') : t('vehicles.expand')}</span>
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
                      {t('vehicles.statusLabel', { status: STATUS_LABEL[inspectionStatus.inspection_status] || statusConfig.label })}
                    </p>
                    {inspectionStatus.days_to_inspection != null && (
                      <p className="text-xs text-gray-500 mt-0.5">
                        {inspectionStatus.days_to_inspection > 0
                          ? t('vehicles.daysToExpiry', { days: inspectionStatus.days_to_inspection })
                          : t('vehicles.overdueDays', { days: Math.abs(inspectionStatus.days_to_inspection) })}
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
                      {t('vehicles.compulsoryStatus', { status: inspectionStatus.has_compulsory_insurance ? t('vehicles.compulsoryActive') : t('vehicles.compulsoryInactive') })}
                    </p>
                    {inspectionStatus.compulsory_expiry && (
                      <p className="text-xs text-gray-500 mt-0.5">
                        {t('vehicles.expireDate', { date: inspectionStatus.compulsory_expiry })}
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
                    {inspectionStatus.can_inspect ? t('vehicles.canInspect') : t('vehicles.cannotInspect')}
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
