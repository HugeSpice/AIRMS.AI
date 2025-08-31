'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Key, Plus, Copy, Trash2, Eye, EyeOff, Check, AlertCircle } from 'lucide-react';
import apiService from '@/services/api';

interface ApiKey {
  id: string;
  user_id: string;
  key_name: string;
  key_prefix: string;
  permissions: string[];
  usage_limit?: number;
  usage_count: number;
  is_active: boolean;
  expires_at?: string;
  last_used_at?: string;
  created_at: string;
  updated_at: string;
}

export default function ApiKeyManager() {
  const { user, generateApiKey, revokeApiKey } = useAuth();
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [showNewKey, setShowNewKey] = useState(false);
  const [newlyGeneratedKey, setNewlyGeneratedKey] = useState<string>('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Fetch API keys when component mounts
  useEffect(() => {
    fetchApiKeys();
  }, []);

  const fetchApiKeys = async () => {
    try {
      const keys = await apiService.getApiKeys();
      setApiKeys(keys);
    } catch (err) {
      console.error('Failed to fetch API keys:', err);
    }
  };

  const handleGenerateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;

    setIsGenerating(true);
    setError('');
    setSuccess('');

    try {
      const response = await generateApiKey(newKeyName.trim());
      if (response) {
        setNewlyGeneratedKey(response.api_key);
        setShowNewKey(true);
        setNewKeyName('');
        setSuccess('API key generated successfully!');
        // Refresh the API keys list
        await fetchApiKeys();
      } else {
        setError('Failed to generate API key');
      }
    } catch (err) {
      setError('Failed to generate API key');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
      return;
    }

    try {
      const success = await revokeApiKey(keyId);
      if (success) {
        setSuccess('API key revoked successfully!');
        // Refresh the API keys list
        await fetchApiKeys();
      } else {
        setError('Failed to revoke API key');
      }
    } catch (err) {
      setError('Failed to revoke API key');
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setSuccess('Copied to clipboard!');
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError('Failed to copy to clipboard');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">API Keys</h2>
          <p className="text-gray-600">Manage your API keys for accessing AIRMS services</p>
        </div>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="flex items-center space-x-2 p-3 bg-green-50 border border-green-200 rounded-md">
          <Check size={20} className="text-green-500" />
          <span className="text-sm text-green-700">{success}</span>
        </div>
      )}

      {error && (
        <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-md">
          <AlertCircle size={20} className="text-red-500" />
          <span className="text-sm text-red-700">{error}</span>
        </div>
      )}

      {/* Generate New Key Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Generate New API Key</h3>
        <form onSubmit={handleGenerateKey} className="flex space-x-4">
          <div className="flex-1">
            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="Enter a name for your API key"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              required
            />
          </div>
          <button
            type="submit"
            disabled={isGenerating || !newKeyName.trim()}
            className="bg-brand-500 text-white px-4 py-2 rounded-md hover:bg-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            <Plus size={20} />
            <span>{isGenerating ? 'Generating...' : 'Generate Key'}</span>
          </button>
        </form>
      </div>

      {/* Newly Generated Key Display */}
      {showNewKey && newlyGeneratedKey && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center space-x-2 mb-4">
            <Key size={20} className="text-green-600" />
            <h3 className="text-lg font-medium text-green-800">New API Key Generated</h3>
          </div>
          <p className="text-sm text-green-700 mb-4">
            <strong>Important:</strong> This is the only time you'll see this API key. Please copy it and store it securely.
          </p>
          <div className="flex items-center space-x-2 p-3 bg-white border border-green-300 rounded-md">
            <input
              type={showNewKey ? 'text' : 'password'}
              value={newlyGeneratedKey}
              readOnly
              className="flex-1 bg-transparent text-green-800 font-mono text-sm focus:outline-none"
            />
            <button
              onClick={() => setShowNewKey(!showNewKey)}
              className="text-green-600 hover:text-green-800 p-1"
            >
              {showNewKey ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
            <button
              onClick={() => copyToClipboard(newlyGeneratedKey)}
              className="text-green-600 hover:text-green-800 p-1"
            >
              <Copy size={16} />
            </button>
          </div>
          <button
            onClick={() => setShowNewKey(false)}
            className="mt-4 text-sm text-green-600 hover:text-green-800 underline"
          >
            Hide this key
          </button>
        </div>
      )}

      {/* Existing API Keys */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Your API Keys</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {apiKeys && apiKeys.length > 0 ? (
            apiKeys.map((apiKey: ApiKey) => (
              <div key={apiKey.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <Key size={20} className="text-gray-400" />
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">{apiKey.key_name}</h4>
                        <p className="text-xs text-gray-500">
                          Created: {formatDate(apiKey.created_at)}
                          {apiKey.last_used_at && ` • Last used: ${formatDate(apiKey.last_used_at)}`}
                        </p>
                        <p className="text-xs text-gray-400">
                          Usage: {apiKey.usage_count}/{apiKey.usage_limit || '∞'}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded-full ${
                        apiKey.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {apiKey.is_active ? 'Active' : 'Inactive'}
                    </span>
                    <button
                      onClick={() => handleRevokeKey(apiKey.id)}
                      className="text-red-600 hover:text-red-800 p-1"
                      title="Revoke key"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="px-6 py-8 text-center">
              <Key size={48} className="text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No API keys generated yet</p>
              <p className="text-sm text-gray-400">Generate your first API key above to get started</p>
            </div>
          )}
        </div>
      </div>

      {/* Usage Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-800 mb-3">How to Use Your API Key</h3>
        <div className="text-sm text-blue-700 space-y-2">
          <p>Include your API key in the Authorization header of your requests:</p>
          <code className="block bg-blue-100 px-3 py-2 rounded font-mono text-xs">
            Authorization: Bearer YOUR_API_KEY_HERE
          </code>
          <p className="mt-3">
            <strong>Example:</strong> Use this key to authenticate requests to AIRMS risk detection endpoints.
          </p>
        </div>
      </div>
    </div>
  );
}
