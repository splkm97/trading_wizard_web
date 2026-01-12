import { useNavigate } from 'react-router-dom';
import { Button } from '../components/common';
import { GuideContent } from '../components/guide';

const GUIDE_SEEN_KEY = 'guide_seen';

export function GuidePage() {
  const navigate = useNavigate();

  const handleComplete = () => {
    localStorage.setItem(GUIDE_SEEN_KEY, 'true');
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">시작하기</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Trading Wizard 사용 가이드</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        <GuideContent />

        {/* Complete Button */}
        <div className="mt-12 pb-8 flex justify-center">
          <Button variant="primary" size="lg" onClick={handleComplete}>
            시작하기 완료
          </Button>
        </div>
      </main>
    </div>
  );
}

export { GUIDE_SEEN_KEY };
