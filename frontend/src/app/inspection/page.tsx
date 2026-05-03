'use client';

import { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  MapPin, Search, Navigation, Phone, ExternalLink,
  ChevronLeft, Building2, CarFront, Loader2, Filter, X,
} from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api-client';

interface Station {
  id: string;
  station_name: string;
  station_type: string;
  address: string | null;
  city: string | null;
  district: string | null;
  phone: string | null;
  latitude: number | null;
  longitude: number | null;
  operating_hours: string | null;
  supports_motorcycle: boolean;
  supports_heavy: boolean;
  booking_url: string | null;
  services: string | null;
  distance_km: number | null;
  google_map_url: string | null;
}

type StationType = '' | 'supervision' | 'inspection' | 'private';

const TYPE_LABELS: Record<string, { label: string; color: string; bg: string }> = {
  supervision: { label: '監理站', color: 'text-blue-700', bg: 'bg-blue-50 border-blue-200' },
  inspection: { label: '公立驗車', color: 'text-green-700', bg: 'bg-green-50 border-green-200' },
  private: { label: '民間驗車', color: 'text-orange-700', bg: 'bg-orange-50 border-orange-200' },
};

export default function InspectionPage() {
  const [keyword, setKeyword] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [selectedType, setSelectedType] = useState<StationType>('');
  const [userLat, setUserLat] = useState<number | null>(null);
  const [userLon, setUserLon] = useState<number | null>(null);
  const [locating, setLocating] = useState(false);
  const [locError, setLocError] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const requestLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setLocError('您的瀏覽器不支援定位功能');
      return;
    }
    setLocating(true);
    setLocError('');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLat(pos.coords.latitude);
        setUserLon(pos.coords.longitude);
        setLocating(false);
      },
      (err) => {
        setLocError(err.code === 1 ? '請允許定位權限以顯示附近站點' : '無法取得位置');
        setLocating(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, []);

  // Auto-detect location on mount
  useEffect(() => {
    requestLocation();
  }, [requestLocation]);

  // Fetch cities
  const { data: cities } = useQuery({
    queryKey: ['inspection-cities'],
    queryFn: async () => {
      const res = await api.get('/api/v1/inspection-stations/cities');
      return res.data.data as string[];
    },
    staleTime: 60000,
  });

  // Fetch stations
  const { data: stations, isLoading } = useQuery({
    queryKey: ['inspection-stations', keyword, selectedCity, selectedType, userLat, userLon],
    queryFn: async () => {
      const params: Record<string, string | number> = {};
      if (keyword) params.keyword = keyword;
      if (selectedCity) params.city = selectedCity;
      if (selectedType) params.station_type = selectedType;
      if (userLat && userLon) {
        params.latitude = userLat;
        params.longitude = userLon;
        params.radius_km = 100;
      }
      const res = await api.get('/api/v1/inspection-stations/search', { params });
      return res.data.data as Station[];
    },
    staleTime: 30000,
  });

  const handleSearch = () => {
    setKeyword(searchInput.trim());
  };

  const clearFilters = () => {
    setKeyword('');
    setSearchInput('');
    setSelectedCity('');
    setSelectedType('');
  };

  const hasActiveFilters = keyword || selectedCity || selectedType;

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      {/* Header */}
      <div className="bg-primary-500 text-white px-4 pt-3 pb-5">
        <div className="flex items-center gap-3 mb-4">
          <Link href="/" className="p-1">
            <ChevronLeft className="h-6 w-6" />
          </Link>
          <h1 className="text-lg font-bold flex-1">監理站 / 驗車廠查詢</h1>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2 rounded-lg transition ${showFilters ? 'bg-white/30' : 'bg-white/10'}`}
          >
            <Filter className="h-5 w-5" />
          </button>
        </div>

        {/* Search bar */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="搜尋站名、地址、服務..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full rounded-xl bg-white py-2.5 pl-10 pr-4 text-sm text-gray-900 outline-none placeholder:text-gray-400"
            />
          </div>
          <button
            onClick={handleSearch}
            className="rounded-xl bg-white/20 px-4 text-sm font-medium hover:bg-white/30 transition"
          >
            搜尋
          </button>
        </div>

        {/* Filters panel */}
        {showFilters && (
          <div className="mt-3 space-y-3 bg-white/10 rounded-xl p-3">
            {/* Type filter */}
            <div className="grid grid-cols-4 gap-2">
              <button
                onClick={() => setSelectedType('')}
                className={`rounded-lg py-2 text-xs font-medium transition ${
                  selectedType === '' ? 'bg-white text-primary-500' : 'bg-white/10 text-white'
                }`}
              >
                全部
              </button>
              <button
                onClick={() => setSelectedType('supervision')}
                className={`rounded-lg py-2 text-xs font-medium transition ${
                  selectedType === 'supervision' ? 'bg-white text-blue-600' : 'bg-white/10 text-white'
                }`}
              >
                監理站
              </button>
              <button
                onClick={() => setSelectedType('inspection')}
                className={`rounded-lg py-2 text-xs font-medium transition ${
                  selectedType === 'inspection' ? 'bg-white text-green-600' : 'bg-white/10 text-white'
                }`}
              >
                公立驗車
              </button>
              <button
                onClick={() => setSelectedType('private')}
                className={`rounded-lg py-2 text-xs font-medium transition ${
                  selectedType === 'private' ? 'bg-white text-orange-600' : 'bg-white/10 text-white'
                }`}
              >
                民間驗車
              </button>
            </div>

            {/* City filter */}
            <select
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
              className="w-full rounded-lg bg-white py-2.5 px-3 text-sm text-gray-900 outline-none"
            >
              <option value="">全部縣市</option>
              {cities?.map((city) => (
                <option key={city} value={city}>{city}</option>
              ))}
            </select>

            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="flex items-center gap-1 text-xs text-white/70 hover:text-white transition"
              >
                <X className="h-3 w-3" /> 清除所有篩選
              </button>
            )}
          </div>
        )}
      </div>

      {/* Location bar */}
      <div className="px-4 py-2 bg-white border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Navigation className="h-4 w-4 text-primary-500" />
            {locating ? (
              <span className="flex items-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" /> 定位中...
              </span>
            ) : userLat ? (
              <span>已定位 - 依距離排序</span>
            ) : (
              <span className="text-gray-400">{locError || '未定位'}</span>
            )}
          </div>
          {!locating && (
            <button
              onClick={requestLocation}
              className="text-xs text-primary-500 font-medium hover:underline"
            >
              {userLat ? '重新定位' : '開啟定位'}
            </button>
          )}
        </div>
      </div>

      {/* Results count */}
      <div className="px-4 py-2">
        <p className="text-xs text-gray-500">
          {isLoading ? '搜尋中...' : `共找到 ${stations?.length ?? 0} 個站點`}
          {hasActiveFilters && (
            <span className="text-primary-500 ml-1">
              (已篩選{selectedCity ? ` ${selectedCity}` : ''}{selectedType ? ` ${TYPE_LABELS[selectedType]?.label}` : ''}{keyword ? ` "${keyword}"` : ''})
            </span>
          )}
        </p>
      </div>

      {/* Station list */}
      <div className="px-4 space-y-3">
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
          </div>
        ) : !stations?.length ? (
          <div className="text-center py-12">
            <MapPin className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-400 text-sm">找不到符合條件的站點</p>
            <button onClick={clearFilters} className="mt-2 text-sm text-primary-500">
              清除篩選條件
            </button>
          </div>
        ) : (
          stations.map((station) => (
            <StationCard key={station.id} station={station} />
          ))
        )}
      </div>
    </div>
  );
}

function StationCard({ station }: { station: Station }) {
  const typeInfo = TYPE_LABELS[station.station_type] || TYPE_LABELS.inspection;
  const services = station.services?.split(',').map((s) => s.trim()).filter(Boolean) ?? [];

  return (
    <div className="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
      {/* Top section */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${typeInfo.bg} ${typeInfo.color}`}>
                {station.station_type === 'supervision' ? (
                  <Building2 className="h-3 w-3" />
                ) : (
                  <CarFront className="h-3 w-3" />
                )}
                {typeInfo.label}
              </span>
              {station.distance_km != null && (
                <span className="text-[11px] text-gray-400 font-medium">
                  {station.distance_km < 1
                    ? `${Math.round(station.distance_km * 1000)}m`
                    : `${station.distance_km}km`}
                </span>
              )}
            </div>
            <h3 className="font-bold text-gray-900 text-sm">{station.station_name}</h3>
          </div>
        </div>

        {/* Address */}
        {station.address && (
          <p className="text-xs text-gray-500 mb-2 flex items-start gap-1.5">
            <MapPin className="h-3.5 w-3.5 text-gray-400 mt-0.5 shrink-0" />
            {station.address}
          </p>
        )}

        {/* Operating hours */}
        {station.operating_hours && (
          <p className="text-xs text-gray-400 mb-2">
            {station.operating_hours}
          </p>
        )}

        {/* Services tags */}
        {services.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {services.map((svc, i) => (
              <span
                key={i}
                className="inline-block rounded-md bg-gray-100 px-2 py-0.5 text-[10px] text-gray-600"
              >
                {svc}
              </span>
            ))}
            {station.supports_motorcycle && (
              <span className="inline-block rounded-md bg-yellow-50 border border-yellow-200 px-2 py-0.5 text-[10px] text-yellow-700">
                機車
              </span>
            )}
            {station.supports_heavy && (
              <span className="inline-block rounded-md bg-purple-50 border border-purple-200 px-2 py-0.5 text-[10px] text-purple-700">
                大型車
              </span>
            )}
          </div>
        )}
      </div>

      {/* Bottom action bar */}
      <div className="flex border-t border-gray-100 divide-x divide-gray-100">
        {/* Phone */}
        {station.phone && (
          <a
            href={`tel:${station.phone}`}
            className="flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-medium text-primary-500 hover:bg-gray-50 transition"
          >
            <Phone className="h-3.5 w-3.5" />
            {station.phone}
          </a>
        )}

        {/* Google Maps navigation */}
        {station.google_map_url && (
          <a
            href={station.google_map_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-medium text-green-600 hover:bg-gray-50 transition"
          >
            <Navigation className="h-3.5 w-3.5" />
            Google Map 導航
          </a>
        )}

        {/* Booking */}
        {station.booking_url && (
          <a
            href={station.booking_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-medium text-accent-500 hover:bg-gray-50 transition"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            線上預約
          </a>
        )}
      </div>
    </div>
  );
}
