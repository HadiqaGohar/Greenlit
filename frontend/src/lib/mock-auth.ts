// Mock authentication service for demo purposes
// This can be easily swapped with real Firebase auth

interface MockUser {
  uid: string;
  email: string;
  displayName?: string;
  photoURL?: string;
}

class MockAuthService {
  private user: MockUser | null = null;
  private listeners: ((user: MockUser | null) => void)[] = [];

  constructor() {
    // Check localStorage for persisted user
    if (typeof window !== 'undefined') {
      const savedUser = localStorage.getItem('mockUser');
      if (savedUser) {
        this.user = JSON.parse(savedUser);
      }
    }
  }

  onAuthStateChanged(callback: (user: MockUser | null) => void) {
    this.listeners.push(callback);
    callback(this.user);
    
    return () => {
      this.listeners = this.listeners.filter(listener => listener !== callback);
    };
  }

  async signInWithEmailAndPassword(email: string, password: string): Promise<void> {
    // Mock validation
    if (password.length < 6) {
      throw new Error('Password should be at least 6 characters');
    }

    const mockUser: MockUser = {
      uid: `mock_${Date.now()}`,
      email,
      displayName: email.split('@')[0]
    };

    this.setUser(mockUser);
  }

  async createUserWithEmailAndPassword(email: string, password: string): Promise<void> {
    // Mock validation
    if (password.length < 6) {
      throw new Error('Password should be at least 6 characters');
    }

    const mockUser: MockUser = {
      uid: `mock_${Date.now()}`,
      email,
      displayName: email.split('@')[0]
    };

    this.setUser(mockUser);
  }

  async signInWithPopup(): Promise<void> {
    const mockUser: MockUser = {
      uid: `google_${Date.now()}`,
      email: 'demo@greenlit-ai.com',
      displayName: 'Demo User',
      photoURL: 'https://via.placeholder.com/40'
    };

    this.setUser(mockUser);
  }

  async signOut(): Promise<void> {
    this.setUser(null);
  }

  private setUser(user: MockUser | null) {
    this.user = user;
    
    if (typeof window !== 'undefined') {
      if (user) {
        localStorage.setItem('mockUser', JSON.stringify(user));
      } else {
        localStorage.removeItem('mockUser');
      }
    }

    this.listeners.forEach(listener => listener(user));
  }

  get currentUser() {
    return this.user;
  }
}

export const mockAuth = new MockAuthService();
export type { MockUser };