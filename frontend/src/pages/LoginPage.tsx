import { useState, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button, Card, Input } from '../components/common';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import {
  generateKeyPair,
  signChallenge,
  computeFingerprint,
  extractPublicKey,
} from '../services/auth';
import { downloadPemFile, readPemFile, validatePemFormat } from '../services/pem';

type Mode = 'login' | 'register';

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [mode, setMode] = useState<Mode>('login');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nickname, setNickname] = useState('');

  // For key generation result
  const [generatedKeys, setGeneratedKeys] = useState<{
    publicKeyPem: string;
    privateKeyPem: string;
    fingerprint: string;
  } | null>(null);

  // File input ref
  const fileInputRef = useRef<HTMLInputElement>(null);

  const from = (location.state as { from?: Location })?.from?.pathname || '/dashboard';

  const handleGenerateKey = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const keys = await generateKeyPair();
      setGeneratedKeys(keys);
    } catch (err) {
      setError('Failed to generate key pair');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadPrivateKey = () => {
    if (generatedKeys) {
      downloadPemFile(generatedKeys.privateKeyPem, 'trading_wizard_private_key.pem');
    }
  };

  const handleRegister = async () => {
    if (!generatedKeys) return;

    setIsLoading(true);
    setError(null);

    try {
      await api.post('/auth/register', {
        public_key: generatedKeys.publicKeyPem,
        nickname: nickname || null,
      });

      // Auto-login after registration
      await performLogin(generatedKeys.privateKeyPem, generatedKeys.fingerprint);
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setError(null);

    try {
      const pemContent = await readPemFile(file);

      if (!validatePemFormat(pemContent, 'PRIVATE KEY')) {
        throw new Error('Invalid PEM file. Please select a valid private key file.');
      }

      // Extract public key and compute fingerprint
      const publicKeyPem = await extractPublicKey(pemContent);
      const fingerprint = await computeFingerprint(publicKeyPem);

      await performLogin(pemContent, fingerprint);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      setError(error.message || error.detail || 'Login failed');
    } finally {
      setIsLoading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const performLogin = async (privateKeyPem: string, fingerprint: string) => {
    // Request challenge
    const challengeResponse = await api.post<{ challenge: string }>('/auth/challenge', {
      fingerprint,
    });

    // Sign challenge
    const signature = await signChallenge(privateKeyPem, challengeResponse.challenge);

    // Verify signature
    const verifyResponse = await api.post<{ access_token: string }>('/auth/verify', {
      fingerprint,
      challenge: challengeResponse.challenge,
      signature,
    });

    // Login successful
    login(verifyResponse.access_token, fingerprint);
    navigate(from, { replace: true });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
      <Card className="w-full max-w-md">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-800">Trading Wizard Web</h1>
          <p className="text-gray-600 mt-1">PEM 키 기반 인증</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Mode Toggle */}
        <div className="flex mb-6 border-b border-gray-200">
          <button
            className={`flex-1 py-2 text-center ${
              mode === 'login'
                ? 'border-b-2 border-primary-600 text-primary-600 font-medium'
                : 'text-gray-500'
            }`}
            onClick={() => setMode('login')}
          >
            로그인
          </button>
          <button
            className={`flex-1 py-2 text-center ${
              mode === 'register'
                ? 'border-b-2 border-primary-600 text-primary-600 font-medium'
                : 'text-gray-500'
            }`}
            onClick={() => setMode('register')}
          >
            회원가입
          </button>
        </div>

        {mode === 'login' ? (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              PEM 개인키 파일을 업로드하여 로그인하세요.
            </p>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pem"
              onChange={handleFileSelect}
              className="hidden"
            />

            <Button
              onClick={() => fileInputRef.current?.click()}
              isLoading={isLoading}
              className="w-full"
            >
              PEM 파일 선택
            </Button>

            <p className="text-xs text-gray-500 text-center">
              개인키 파일을 분실한 경우 복구가 불가능합니다.
              <br />새 키를 생성하여 다시 등록해주세요.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {!generatedKeys ? (
              <>
                <p className="text-sm text-gray-600">
                  새 키 쌍을 생성하여 계정을 만드세요. 생성된 개인키는 안전하게 보관하세요.
                </p>

                <Button
                  onClick={handleGenerateKey}
                  isLoading={isLoading}
                  className="w-full"
                >
                  새 키 생성
                </Button>
              </>
            ) : (
              <>
                <div className="p-3 bg-green-100 text-green-700 rounded-lg text-sm">
                  키가 생성되었습니다! 개인키를 다운로드하고 안전하게 보관하세요.
                </div>

                <div className="p-3 bg-gray-100 rounded-lg">
                  <p className="text-xs text-gray-500 mb-1">Fingerprint</p>
                  <p className="text-xs font-mono break-all">{generatedKeys.fingerprint}</p>
                </div>

                <Button
                  onClick={handleDownloadPrivateKey}
                  variant="secondary"
                  className="w-full"
                >
                  개인키 다운로드
                </Button>

                <Input
                  label="닉네임 (선택)"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  placeholder="표시용 이름"
                  maxLength={50}
                />

                <Button
                  onClick={handleRegister}
                  isLoading={isLoading}
                  className="w-full"
                >
                  등록 완료
                </Button>

                <p className="text-xs text-red-500 text-center">
                  ⚠️ 개인키를 분실하면 계정에 접근할 수 없습니다!
                </p>
              </>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
