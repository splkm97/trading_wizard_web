import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SettingsForm } from '../components/settings/SettingsForm';
import { UserSettings, ConstitutionWarning } from '../types';
import { api } from '../services/api';

type SettingsTab = 'risk' | 'bollinger' | 'contrarian' | 'advanced';

export function SettingsPage() {
  const [searchParams] = useSearchParams();
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get initial tab from URL query parameter
  const tabParam = searchParams.get('tab');
  const initialTab: SettingsTab = ['risk', 'bollinger', 'contrarian', 'advanced'].includes(tabParam || '')
    ? (tabParam as SettingsTab)
    : 'risk';

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const data = await api.get<UserSettings>('/settings');
      setSettings(data);
    } catch (err) {
      setError('설정을 불러오는데 실패했습니다.');
      console.error('Failed to fetch settings:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async (newSettings: UserSettings): Promise<ConstitutionWarning[]> => {
    try {
      const response = await api.put<{
        settings: UserSettings;
        warnings: ConstitutionWarning[];
      }>('/settings', newSettings);

      setSettings(response.settings);
      return response.warnings;
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'detail' in err
        ? (err as { detail: string }).detail
        : '설정 저장에 실패했습니다.';
      throw new Error(message);
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">설정</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {settings && (
        <div className="max-w-xl">
          <SettingsForm
            initialSettings={settings}
            onSave={handleSave}
            isLoading={isLoading}
            initialTab={initialTab}
          />
        </div>
      )}
    </div>
  );
}
