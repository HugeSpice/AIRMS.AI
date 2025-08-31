import AppWrapper from '@/components/AppWrapper';
import ProtectedRoute from '@/components/ProtectedRoute';
import ApiKeyManager from '@/components/ApiKeyManager';

function ApiKeysContent() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-8 px-4">
        <ApiKeyManager />
      </div>
    </div>
  );
}

export default function ApiKeysPage() {
  return (
    <AppWrapper>
      <ProtectedRoute>
        <ApiKeysContent />
      </ProtectedRoute>
    </AppWrapper>
  );
}
