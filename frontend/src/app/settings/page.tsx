'use client';

import AppWrapper from '@/components/AppWrapper';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useState } from 'react';
import {
  Settings as SettingsIcon,
  Shield,
  Database,
  Bell,
  User,
  Key,
  Globe
} from 'lucide-react';

function SettingsContent() {
  const [activeTab, setActiveTab] = useState('general');
  const [generalSettings, setGeneralSettings] = useState({
    notifications: true,
    autoScan: true,
    riskThreshold: 'medium'
  });

  const tabs = [
    { id: 'general', name: 'General', icon: SettingsIcon },
    { id: 'security', name: 'Security', icon: Shield },
    { id: 'notifications', name: 'Notifications', icon: Bell },
    { id: 'integrations', name: 'Integrations', icon: Database }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600">Configure your AIRMS preferences and security settings</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm">
          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                      activeTab === tab.id
                        ? 'border-brand-500 text-brand-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{tab.name}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'general' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">General Settings</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">Email Notifications</label>
                        <p className="text-sm text-gray-500">Receive email alerts for important events</p>
                      </div>
                      <button
                        onClick={() => setGeneralSettings(prev => ({ ...prev, notifications: !prev.notifications }))}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          generalSettings.notifications ? 'bg-brand-500' : 'bg-gray-200'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            generalSettings.notifications ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">Auto Risk Scanning</label>
                        <p className="text-sm text-gray-500">Automatically scan content for risks</p>
                      </div>
                      <button
                        onClick={() => setGeneralSettings(prev => ({ ...prev, autoScan: !prev.autoScan }))}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          generalSettings.autoScan ? 'bg-brand-500' : 'bg-gray-200'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            generalSettings.autoScan ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Risk Threshold</label>
                      <select
                        value={generalSettings.riskThreshold}
                        onChange={(e) => setGeneralSettings(prev => ({ ...prev, riskThreshold: e.target.value }))}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-brand-500 focus:border-brand-500"
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Security Settings</h3>
                  <div className="space-y-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <Shield className="h-5 w-5 text-blue-500" />
                        <div>
                          <h4 className="text-sm font-medium text-blue-800">Two-Factor Authentication</h4>
                          <p className="text-sm text-blue-700">Add an extra layer of security to your account</p>
                        </div>
                      </div>
                      <button className="mt-3 bg-blue-500 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-600 transition-colors">
                        Enable 2FA
                      </button>
                    </div>

                    <div className="p-4 bg-green-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <Key className="h-5 w-5 text-green-500" />
                        <div>
                          <h4 className="text-sm font-medium text-green-800">API Key Management</h4>
                          <p className="text-sm text-green-700">Manage your API keys and permissions</p>
                        </div>
                      </div>
                      <button className="mt-3 bg-green-500 text-white px-4 py-2 rounded-md text-sm hover:bg-green-600 transition-colors">
                        Manage Keys
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Notification Preferences</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">High Risk Alerts</label>
                        <p className="text-sm text-gray-500">Immediate notifications for critical risks</p>
                      </div>
                      <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-brand-500">
                        <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-6" />
                      </button>
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">Weekly Reports</label>
                        <p className="text-sm text-gray-500">Summary of weekly risk assessments</p>
                      </div>
                      <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-200">
                        <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-1" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'integrations' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Data Integrations</h3>
                  <div className="space-y-4">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <Database className="h-5 w-5 text-gray-500" />
                        <div>
                          <h4 className="text-sm font-medium text-gray-800">Database Connections</h4>
                          <p className="text-sm text-gray-600">Connect to external databases for risk analysis</p>
                        </div>
                      </div>
                      <button className="mt-3 bg-gray-500 text-white px-4 py-2 rounded-md text-sm hover:bg-gray-600 transition-colors">
                        Add Connection
                      </button>
                    </div>

                    <div className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <Globe className="h-5 w-5 text-gray-500" />
                        <div>
                          <h4 className="text-sm font-medium text-gray-800">API Integrations</h4>
                          <p className="text-sm text-gray-600">Connect to third-party services and APIs</p>
                        </div>
                      </div>
                      <button className="mt-3 bg-gray-500 text-white px-4 py-2 rounded-md text-sm hover:bg-gray-600 transition-colors">
                        Configure APIs
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Settings() {
  return (
    <AppWrapper>
      <ProtectedRoute>
        <SettingsContent />
      </ProtectedRoute>
    </AppWrapper>
  );
}
