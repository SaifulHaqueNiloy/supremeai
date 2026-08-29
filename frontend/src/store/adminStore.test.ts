import { describe, it, expect, vi, beforeEach } from 'vitest';

const { fakeAuth } = vi.hoisted(() => ({
  fakeAuth: {
    currentUser: {
      getIdToken: vi.fn().mockResolvedValue('id-token'),
      email: 'a@b.com',
    },
  },
}));

vi.mock('../firebase', () => ({
  getFirebaseAuth: vi.fn().mockResolvedValue(fakeAuth),
}));

vi.mock('firebase/auth', () => ({
  signInWithEmailAndPassword: vi.fn(),
  signOut: vi.fn().mockResolvedValue(undefined),
}));

import { signInWithEmailAndPassword, signOut } from 'firebase/auth';
import { eventBus, Events } from '../lib/componentEventBus';

const { firebaseLogin, firebaseTotpSetup, firebaseTotpVerify } = vi.hoisted(() => ({
  firebaseLogin: vi.fn(),
  firebaseTotpSetup: vi.fn(),
  firebaseTotpVerify: vi.fn(),
}));

vi.mock('../services/authService', () => ({
  authService: {
    firebaseLogin,
    firebaseTotpSetup,
    firebaseTotpVerify,
  },
}));

import { useAdminStore } from './adminStore';
import { Events } from '../lib/componentEventBus';

const reset = () =>
  useAdminStore.setState({
    adminAuthenticated: false,
    adminRole: null,
    adminError: '',
    actionStatus: '',
    adminSubTab: 'dashboard',
    adminEmail: '',
    otpRequired: false,
    adminOtp: '',
    totpSetupRequired: false,
    totpSecret: '',
    provisioningUri: '',
  });

describe('adminStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    reset();
    (signInWithEmailAndPassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      user: { getIdToken: () => Promise.resolve('id-token') },
    });
  });

  it('sets scalar admin fields', () => {
    useAdminStore.getState().setAdminRole('superadmin');
    useAdminStore.getState().setAdminError('err');
    useAdminStore.getState().setActionStatus('busy');
    useAdminStore.getState().setAdminSubTab('users');
    useAdminStore.getState().setAdminEmail('a@b.com');
    useAdminStore.getState().setOtpRequired(true);
    useAdminStore.getState().setAdminOtp('123456');
    useAdminStore.getState().setTotpSetupRequired(true);
    useAdminStore.getState().setTotpSecret('secret');
    useAdminStore.getState().setProvisioningUri('uri');
    const s = useAdminStore.getState();
    expect(s.adminRole).toBe('superadmin');
    expect(s.adminError).toBe('err');
    expect(s.actionStatus).toBe('busy');
    expect(s.adminSubTab).toBe('users');
    expect(s.adminEmail).toBe('a@b.com');
    expect(s.otpRequired).toBe(true);
    expect(s.adminOtp).toBe('123456');
    expect(s.totpSetupRequired).toBe(true);
    expect(s.totpSecret).toBe('secret');
    expect(s.provisioningUri).toBe('uri');
  });

  it('returns early from login when email/password are missing', async () => {
    await useAdminStore.getState().handleAdminLogin();
    expect(firebaseLogin).not.toHaveBeenCalled();
  });

  it('records a firebase auth error', async () => {
    useAdminStore.getState().setAdminEmail('a@b.com');
    (signInWithEmailAndPassword as unknown as ReturnType<typeof vi.fn>).mockRejectedValue({
      message: 'bad creds',
    });
    await useAdminStore.getState().handleAdminLogin('pw');
    expect(useAdminStore.getState().adminError).toContain('bad creds');
  });

  it('requires OTP when the backend reports otp_required', async () => {
    useAdminStore.getState().setAdminEmail('a@b.com');
    firebaseLogin.mockResolvedValue({ status: 'otp_required' });
    await useAdminStore.getState().handleAdminLogin('pw');
    expect(useAdminStore.getState().otpRequired).toBe(true);
  });

  it('starts TOTP setup when backend reports totp_setup_required', async () => {
    useAdminStore.getState().setAdminEmail('a@b.com');
    firebaseLogin.mockResolvedValue({ status: 'totp_setup_required' });
    firebaseTotpSetup.mockResolvedValue({ secret: 's3cr3t' });
    await useAdminStore.getState().handleAdminLogin('pw');
    const s = useAdminStore.getState();
    expect(s.totpSetupRequired).toBe(true);
    expect(s.totpSecret).toBe('s3cr3t');
    expect(s.provisioningUri).toContain('otpauth');
  });

  it('authenticates after verifying the TOTP code', async () => {
    useAdminStore.setState({ adminEmail: 'a@b.com', otpRequired: true, adminOtp: '123456' });
    const payload = Buffer.from(JSON.stringify({ role: 'admin' }))
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
    firebaseTotpVerify.mockResolvedValue({ token: `h.${payload}.s` });
    await useAdminStore.getState().handleAdminLogin('pw');
    const s = useAdminStore.getState();
    expect(s.adminAuthenticated).toBe(true);
    expect(s.adminRole).toBe('admin');
    expect(localStorage.getItem('supreme_admin_jwt')).toBe(`h.${payload}.s`);
  });

  it('records an error when TOTP verification fails', async () => {
    useAdminStore.setState({ adminEmail: 'a@b.com', otpRequired: true, adminOtp: '000000' });
    firebaseTotpVerify.mockRejectedValue({ message: 'invalid code' });
    await useAdminStore.getState().handleAdminLogin('pw');
    expect(useAdminStore.getState().adminError).toContain('invalid code');
    expect(useAdminStore.getState().adminAuthenticated).toBe(false);
  });

  it('logs out, clears tokens and emits AUTH_LOGOUT', async () => {
    let emitted = false;
    const handler = () => {
      emitted = true;
    };
    eventBus.on(Events.AUTH_LOGOUT, handler);
    localStorage.setItem('supreme_admin_jwt', 'x');
    await useAdminStore.getState().handleAdminLogout();
    expect(localStorage.getItem('supreme_admin_jwt')).toBeNull();
    expect(signOut).toHaveBeenCalled();
    expect(emitted).toBe(true);
    expect(useAdminStore.getState().adminAuthenticated).toBe(false);
  });
});
