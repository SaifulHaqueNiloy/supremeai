import React, { useState } from 'react';
import { apiClient } from '../../services/apiClient';

type DiscoveredTool = {
    name: string;
    description?: string;
};

export const MCPConnector: React.FC = () => {
    const [mcpUrl, setMcpUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [discoveredTools, setDiscoveredTools] = useState<DiscoveredTool[] | null>(null);

    const handleConnect = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setDiscoveredTools(null);

        try {
            const data = await apiClient.post<{ status: string; tools: DiscoveredTool[] }>('/api/v1/mcp/discover', {
                mcp_url: mcpUrl,
            });
            setDiscoveredTools(data.tools);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="border border-gray-200 rounded-xl p-6 bg-white shadow-sm mt-8">
            <h2 className="text-xl font-bold mb-2">Connect Custom MCP Server</h2>
            <p className="text-sm text-gray-600 mb-6">
                Connect your own Model Context Protocol (MCP) compatible server to add custom tools.
            </p>

            <form onSubmit={handleConnect} className="flex gap-4 mb-6">
                <input 
                    type="url" 
                    value={mcpUrl}
                    onChange={(e) => setMcpUrl(e.target.value)}
                    placeholder="https://your-mcp-server.com"
                    required
                    className="flex-grow border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-black outline-none"
                />
                <button 
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2 bg-black text-white rounded-lg font-medium disabled:opacity-50"
                >
                    {loading ? 'Connecting...' : 'Connect'}
                </button>
            </form>

            {error && (
                <div role="alert" className="bg-red-50 text-red-700 p-4 rounded-lg mb-4 text-sm">
                    {error}
                </div>
            )}

            {discoveredTools && (
                <div className="bg-green-50 border border-green-100 rounded-lg p-4">
                    <h3 className="text-green-800 font-semibold mb-2">Connection Successful!</h3>
                    <p className="text-sm text-green-700 mb-2">Discovered {discoveredTools.length} tools:</p>
                    <ul className="list-disc list-inside text-sm text-green-700">
                        {discoveredTools.map((t, i) => (
                            <li key={i}>{t.name}</li>
                        ))}
                    </ul>
                    <button className="mt-4 px-4 py-2 bg-green-600 text-white rounded font-medium text-sm hover:bg-green-700 transition">
                        Install as Private Plugin
                    </button>
                </div>
            )}
        </div>
    );
};
