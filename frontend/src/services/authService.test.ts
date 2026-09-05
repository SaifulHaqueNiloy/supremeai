import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('./apiClient', () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

import { authService } from './authService';
import { apiClient } from './apiClient';

describe('authService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('firebaseLogin posts the id_token', async () => {
    (apiClient.post as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      status: 'ok',
      token: 't',
      uid: 'u',
      email: 'e',
    });
    const res = await authService.firebaseLogin('idt');
    expect(apiClient.post).toHaveBeenCalledWith('/api/admin/firebase-login', {
      id_token: 'idt',
    });
    expect(res.token).toBe('t');
  });

  it('firebaseTotpSetup posts the id_token', async () => {
    (apiClient.post as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      secret: 's',
      provisioning_uri: 'uri',
    });
    const res = await authService.firebaseTotpSetup('idt');
    expect(apiClient.post).toHaveBeenCalledWith('/api/admin/firebase-totp-setup', {
      id_token: 'idt',
    });
    expect(res.secret).toBe('s');
  });

  it('firebaseTotpVerify posts the id_token, otp, and remember_browser flag', async () => {
    (apiClient.post as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      status: 'ok',
      token: 'tok',
    });
    const res = await authService.firebaseTotpVerify('idt', '123456');
    expect(apiClient.post).toHaveBeenCalledWith('/api/admin/firebase-totp-verify', {
      id_token: 'idt',
      otp: '123456',
      remember_browser: false,
    });
    expect(res.token).toBe('tok');

    // Test with rememberBrowser = true
    await authService.firebaseTotpVerify('idt', '123456', true);
    expect(apiClient.post).toHaveBeenCalledWith('/api/admin/firebase-totp-verify', {
      id_token: 'idt',
      otp: '123456',
      remember_browser: true,
    });
  });
});
