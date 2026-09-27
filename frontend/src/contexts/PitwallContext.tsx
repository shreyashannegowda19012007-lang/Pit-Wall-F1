import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

type ApiStatus = 'connecting' | 'healthy' | 'error';

interface PitwallContextType {
  session: string;
  setSession: (session: string) => void;
  primaryDriver: string;
  setPrimaryDriver: (driver: string) => void;
  referenceDriver: string;
  setReferenceDriver: (driver: string) => void;
  apiStatus: ApiStatus;
}

const PitwallContext = createContext<PitwallContextType | undefined>(undefined);

export function PitwallProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState('S-2024-SPAIN');
  const [primaryDriver, setPrimaryDriver] = useState('VER');
  const [referenceDriver, setReferenceDriver] = useState('HAM');
  const [apiStatus, setApiStatus] = useState<ApiStatus>('connecting');

  useEffect(() => {
    fetch('http://localhost:8000/api/health')
      .then(res => res.json())
      .then(() => setApiStatus('healthy'))
      .catch(() => setApiStatus('error'));
  }, []);

  return (
    <PitwallContext.Provider
      value={{
        session, setSession,
        primaryDriver, setPrimaryDriver,
        referenceDriver, setReferenceDriver,
        apiStatus
      }}
    >
      {children}
    </PitwallContext.Provider>
  );
}

export function usePitwall() {
  const context = useContext(PitwallContext);
  if (context === undefined) {
    throw new Error('usePitwall must be used within a PitwallProvider');
  }
  return context;
}
