import { useState, useEffect } from 'react';

const DISCLAIMER_KEY = 'disclaimer_accepted';

export function Disclaimer() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const accepted = localStorage.getItem(DISCLAIMER_KEY);
    if (!accepted) {
      setShow(true);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem(DISCLAIMER_KEY, 'true');
    setShow(false);
  };

  if (!show) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
        <h2 className="text-xl font-bold text-red-600 mb-4">
          ⚠️ 투자 위험 고지
        </h2>
        
        <div className="text-gray-700 space-y-3 mb-6">
          <p>
            본 서비스는 <strong>투자 참고 정보</strong>를 제공할 뿐이며, 
            투자 권유나 조언을 목적으로 하지 않습니다.
          </p>
          <p>
            모든 투자 결정과 그에 따른 <strong>손익의 책임은 전적으로 투자자 본인</strong>에게 있습니다.
          </p>
          <p>
            과거의 수익률이 미래의 수익을 보장하지 않으며, 
            원금 손실이 발생할 수 있습니다.
          </p>
          <p className="text-sm text-gray-500">
            본 서비스 이용으로 인한 투자 손실에 대해 
            개발자 및 서비스 제공자는 어떠한 책임도 지지 않습니다.
          </p>
        </div>

        <button
          onClick={handleAccept}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          위 내용을 이해하고 동의합니다
        </button>
      </div>
    </div>
  );
}
