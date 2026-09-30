import { useState, useCallback, useEffect } from 'react';
import { apiClient } from '../services/apiClient';

export interface PluginManifest {
    id: string;
    name: string;
    description: string;
    icon_url: string;
    category: string;
    source: string;
    auth_type: string;
}

export interface UserPluginInstallation {
    id: string;
    plugin_id: string;
    status: string;
    is_enabled: boolean;
}

export const usePlugins = () => {
    const [marketplacePlugins, setMarketplacePlugins] = useState<PluginManifest[]>([]);
    const [installedPlugins, setInstalledPlugins] = useState<UserPluginInstallation[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchPlugins = useCallback(async () => {
        try {
            setLoading(true);
            
            // বাংলা মন্তব্য (#2522): raw fetch() → apiClient — auth header, timeout,
            // 429/402 error-normalization এখন কেন্দ্রীয় ট্রান্সপোর্ট থেকে।
            const [marketData, installedData] = await Promise.all([
                apiClient.get<{ plugins?: PluginManifest[] }>('/api/v1/plugins/marketplace').catch(() => null),
                apiClient.get<{ installations?: UserPluginInstallation[] }>('/api/v1/plugins/installed').catch(() => null),
            ]);
            if (marketData) setMarketplacePlugins(marketData.plugins || []);
            if (installedData) setInstalledPlugins(installedData.installations || []);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : String(err));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchPlugins();
    }, [fetchPlugins]);

    const installPlugin = async (pluginId: string, capabilities: string[]) => {
        try {
            // বাংলা মন্তব্য (#2522): raw fetch() → apiClient.post — !ok হলে ApiError throw হয়।
            await apiClient.post('/api/v1/plugins/install', { plugin_id: pluginId, granted_capabilities: capabilities });
            await fetchPlugins();
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : String(err));
            throw err;
        }
    };

    const uninstallPlugin = async (pluginId: string) => {
        try {
            // বাংলা মন্তব্য (#2522): raw fetch() → apiClient.delete
            await apiClient.delete(`/api/v1/plugins/uninstall/${pluginId}`);
            await fetchPlugins();
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : String(err));
            throw err;
        }
    };

    return {
        marketplacePlugins,
        installedPlugins,
        loading,
        error,
        installPlugin,
        uninstallPlugin,
        refresh: fetchPlugins
    };
};
