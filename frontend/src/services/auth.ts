/**
 * Web Crypto API operations for ECDSA P-256 key generation and signing.
 */

import { pemToArrayBuffer, arrayBufferToPem, arrayBufferToBase64 } from './pem';

interface KeyPairResult {
  publicKeyPem: string;
  privateKeyPem: string;
  fingerprint: string;
}

/**
 * Generate ECDSA P-256 key pair using Web Crypto API.
 */
export async function generateKeyPair(): Promise<KeyPairResult> {
  // Generate key pair
  const keyPair = await crypto.subtle.generateKey(
    {
      name: 'ECDSA',
      namedCurve: 'P-256',
    },
    true, // extractable
    ['sign', 'verify']
  );

  // Export public key as SPKI
  const publicKeyBuffer = await crypto.subtle.exportKey('spki', keyPair.publicKey);
  const publicKeyPem = arrayBufferToPem(publicKeyBuffer, 'PUBLIC KEY');

  // Export private key as PKCS8
  const privateKeyBuffer = await crypto.subtle.exportKey('pkcs8', keyPair.privateKey);
  const privateKeyPem = arrayBufferToPem(privateKeyBuffer, 'PRIVATE KEY');

  // Compute fingerprint (SHA-256 of PEM)
  const fingerprintBuffer = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(publicKeyPem)
  );
  const fingerprint = Array.from(new Uint8Array(fingerprintBuffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');

  return { publicKeyPem, privateKeyPem, fingerprint };
}

/**
 * Sign data with private key.
 */
export async function signChallenge(
  privateKeyPem: string,
  challengeBase64: string
): Promise<string> {
  // Import private key
  const privateKeyBuffer = pemToArrayBuffer(privateKeyPem, 'PRIVATE KEY');
  const privateKey = await crypto.subtle.importKey(
    'pkcs8',
    privateKeyBuffer,
    {
      name: 'ECDSA',
      namedCurve: 'P-256',
    },
    false,
    ['sign']
  );

  // Decode challenge
  const challengeBuffer = Uint8Array.from(atob(challengeBase64), (c) => c.charCodeAt(0));

  // Sign
  const signatureBuffer = await crypto.subtle.sign(
    {
      name: 'ECDSA',
      hash: 'SHA-256',
    },
    privateKey,
    challengeBuffer
  );

  // Convert signature to DER format (Web Crypto returns raw r||s format)
  const derSignature = rawSignatureToDer(new Uint8Array(signatureBuffer));

  // Return as base64
  return arrayBufferToBase64(derSignature.buffer as ArrayBuffer);
}

/**
 * Compute fingerprint of a public key.
 */
export async function computeFingerprint(publicKeyPem: string): Promise<string> {
  const fingerprintBuffer = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(publicKeyPem.trim())
  );
  return Array.from(new Uint8Array(fingerprintBuffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Convert raw ECDSA signature (r||s) to DER format.
 * Web Crypto API returns 64 bytes (32 for r, 32 for s) for P-256.
 * DER format is required by cryptography library.
 */
function rawSignatureToDer(raw: Uint8Array): Uint8Array {
  const r = raw.slice(0, 32);
  const s = raw.slice(32, 64);

  // Encode as DER integers (add padding if high bit is set)
  const encodeInteger = (bytes: Uint8Array): Uint8Array => {
    // Remove leading zeros but keep one if the next byte has high bit set
    let start = 0;
    while (start < bytes.length - 1 && bytes[start] === 0 && (bytes[start + 1] & 0x80) === 0) {
      start++;
    }

    const trimmed = bytes.slice(start);
    const needsPadding = (trimmed[0] & 0x80) !== 0;

    const len = trimmed.length + (needsPadding ? 1 : 0);
    const result = new Uint8Array(2 + len);
    result[0] = 0x02; // INTEGER tag
    result[1] = len;
    if (needsPadding) {
      result[2] = 0x00;
      result.set(trimmed, 3);
    } else {
      result.set(trimmed, 2);
    }
    return result;
  };

  const rDer = encodeInteger(r);
  const sDer = encodeInteger(s);

  // Wrap in SEQUENCE
  const seqLen = rDer.length + sDer.length;
  const der = new Uint8Array(2 + seqLen);
  der[0] = 0x30; // SEQUENCE tag
  der[1] = seqLen;
  der.set(rDer, 2);
  der.set(sDer, 2 + rDer.length);

  return der;
}

/**
 * Extract public key from private key PEM.
 */
export async function extractPublicKey(privateKeyPem: string): Promise<string> {
  const privateKeyBuffer = pemToArrayBuffer(privateKeyPem, 'PRIVATE KEY');

  const privateKey = await crypto.subtle.importKey(
    'pkcs8',
    privateKeyBuffer,
    {
      name: 'ECDSA',
      namedCurve: 'P-256',
    },
    true,
    ['sign']
  );

  // Unfortunately, Web Crypto doesn't allow direct extraction of public key from private key
  // We need to export and re-import as JWK to get both parts
  const jwk = await crypto.subtle.exportKey('jwk', privateKey);

  // Create public-only JWK (remove 'd' component)
  const publicJwk = { ...jwk };
  delete publicJwk.d;
  publicJwk.key_ops = ['verify'];

  const publicKey = await crypto.subtle.importKey(
    'jwk',
    publicJwk,
    {
      name: 'ECDSA',
      namedCurve: 'P-256',
    },
    true,
    ['verify']
  );

  const publicKeyBuffer = await crypto.subtle.exportKey('spki', publicKey);
  return arrayBufferToPem(publicKeyBuffer, 'PUBLIC KEY');
}
