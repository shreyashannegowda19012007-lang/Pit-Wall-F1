import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';

export type ApiStatus = 'connecting' | 'healthy' | 'error';

export interface DriverMeta {
  driver_number: string;
  broadcast_name: string;
  abbreviation: string;
  team_name: string;
  team_color: string;
  position: number;
  points?: number;
}

export interface RoundInfo {
  round_number: number;
  event_name: string;
  country: string;
  location: string;
  available_sessions: string[];
}

interface PitwallContextType {
  session: string;
  setSession: (session: string) => void;
  primaryDriver: string;
  setPrimaryDriver: (driver: string) => void;
  referenceDriver: string;
  setReferenceDriver: (driver: string) => void;
  apiStatus: ApiStatus;
  availableDrivers: DriverMeta[];
  season: number;
  setSeason: (season: number) => void;
  availableSeasons: number[];
  rounds: RoundInfo[];
  selectedRound: number;
  setSelectedRound: (round: number) => void;
  sessionType: string;
  setSessionType: (type: string) => void;
  isUplinkSyncing: boolean;
  uplinkNotice: string | null;
  triggerUplink: (overrideRound?: number, overrideSessionType?: string) => Promise<boolean>;
}

const PitwallContext = createContext<PitwallContextType | undefined>(undefined);

export function PitwallProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState('S-2026-UNITED_STATES_GRAND_PRIX');
  const [primaryDriver, setPrimaryDriver] = useState('VER');
  const [referenceDriver, setReferenceDriver] = useState('HAM');
  const [apiStatus, setApiStatus] = useState<ApiStatus>('connecting');
  const [availableDrivers, setAvailableDrivers] = useState<DriverMeta[]>([]);
  
  const [season, setSeasonState] = useState<number>(2026);
  const [availableSeasons, setAvailableSeasons] = useState<number[]>([2026, 2025, 2024, 2023, 2022, 2021]);
  const [rounds, setRounds] = useState<RoundInfo[]>([]);
  const [selectedRound, setSelectedRoundState] = useState<number>(18); // Austin COTA Round 18
  const [sessionType, setSessionTypeState] = useState<string>('R');
  const [isUplinkSyncing, setIsUplinkSyncing] = useState<boolean>(false);
  const [uplinkNotice, setUplinkNotice] = useState<string | null>(null);

  const setSessionType = useCallback((newType: string) => {
    setSessionTypeState(newType);
    const roundObj = rounds.find(r => r.round_number === selectedRound);
    const evName = roundObj ? roundObj.event_name.toUpperCase().replace(/\s+/g, '_') : 'UNITED_STATES_GRAND_PRIX';
    const newSessionId = newType === 'R' ? `S-${season}-${evName}` : `S-${season}-${evName}-${newType}`;
    setSession(newSessionId);
  }, [rounds, selectedRound, season]);

  const setSelectedRound = useCallback((newRound: number) => {
    setSelectedRoundState(newRound);
    const roundObj = rounds.find(r => r.round_number === newRound);
    const evName = roundObj ? roundObj.event_name.toUpperCase().replace(/\s+/g, '_') : `ROUND_${newRound}`;
    const newSessionId = sessionType === 'R' ? `S-${season}-${evName}` : `S-${season}-${evName}-${sessionType}`;
    setSession(newSessionId);
  }, [rounds, sessionType, season]);

  const setSeason = useCallback((newSeason: number) => {
    setSeasonState(newSeason);
    const roundObj = rounds.find(r => r.round_number === selectedRound);
    const evName = roundObj ? roundObj.event_name.toUpperCase().replace(/\s+/g, '_') : 'UNITED_STATES_GRAND_PRIX';
    const newSessionId = sessionType === 'R' ? `S-${newSeason}-${evName}` : `S-${newSeason}-${evName}-${sessionType}`;
    setSession(newSessionId);
  }, [rounds, selectedRound, sessionType]);

  // 1. Initial Health & Season check with periodic heartbeat
  useEffect(() => {
    let mounted = true;
    const checkHealth = () => {
      fetch('/api/health')
        .then(res => res.json())
        .then(() => {
          if (mounted) setApiStatus('healthy');
        })
        .catch(() => {
          if (mounted) setApiStatus('error');
        });
    };

    checkHealth();
    const timer = setInterval(checkHealth, 10000);

    fetch('/api/seasons')
      .then(res => res.json())
      .then(data => {
        if (mounted && Array.isArray(data) && data.length > 0) {
          setAvailableSeasons(data);
        }
      })
      .catch(() => {});

    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, []);

  // 2. Fetch rounds when season changes
  useEffect(() => {
    fetch(`/api/seasons/${season}/rounds`)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setRounds(data);
          if (data.length > 0 && !data.find(r => r.round_number === selectedRound)) {
            setSelectedRound(data[0].round_number);
          }
        }
      })
      .catch(() => {});
  }, [season]);

  // 3. Fetch drivers whenever session changes
  const loadDriversForSession = useCallback(async (sessionId: string) => {
    try {
      const res = await fetch(`/api/drivers?session_id=${sessionId}`);
      const data = await res.json();
      if (data.success && Array.isArray(data.drivers) && data.drivers.length > 0) {
        setAvailableDrivers(data.drivers);
        // Ensure primary/ref driver are in list if possible
        const abbrs = data.drivers.map((d: DriverMeta) => d.abbreviation);
        setPrimaryDriver(prev => abbrs.includes(prev) ? prev : (abbrs[0] || 'VER'));
        setReferenceDriver(prev => abbrs.includes(prev) ? prev : (abbrs[1] || abbrs[0] || 'HAM'));
      }
    } catch {
      // Fallback
    }
  }, []);

  useEffect(() => {
    loadDriversForSession(session);
  }, [session, loadDriversForSession]);

  // 4. Trigger Uplink Preparation action
  const triggerUplink = useCallback(async (overrideRound?: number, overrideSessionType?: string): Promise<boolean> => {
    setIsUplinkSyncing(true);
    setUplinkNotice(null);
    const rNum = overrideRound !== undefined ? overrideRound : selectedRound;
    const sType = overrideSessionType !== undefined ? overrideSessionType : sessionType;

    try {
      const roundObj = rounds.find(r => r.round_number === rNum);
      const evName = roundObj ? roundObj.event_name.toUpperCase().replace(/\s+/g, '_') : `ROUND_${rNum}`;
      const newSessionId = sType === 'R' ? `S-${season}-${evName}` : `S-${season}-${evName}-${sType}`;

      const res = await fetch('/api/sessions/prepare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          season,
          round_number: rNum,
          session_type: sType
        })
      });

      const data = await res.json();
      if (res.ok && data.success) {
        setSession(newSessionId);
        setUplinkNotice(`Synchronized: ${roundObj?.event_name || 'Event'} (${season}) - ${sType}`);
        await loadDriversForSession(newSessionId);
        setIsUplinkSyncing(false);
        return true;
      } else {
        setUplinkNotice(`Notice: ${data.detail || data.error || 'Unable to sync telemetry records'}`);
        setIsUplinkSyncing(false);
        return false;
      }
    } catch (err: any) {
      setUplinkNotice(`Connection Error: ${err.message}`);
      setIsUplinkSyncing(false);
      return false;
    }
  }, [selectedRound, sessionType, season, rounds, loadDriversForSession]);

  return (
    <PitwallContext.Provider
      value={{
        session, setSession,
        primaryDriver, setPrimaryDriver,
        referenceDriver, setReferenceDriver,
        apiStatus,
        availableDrivers,
        season, setSeason,
        availableSeasons,
        rounds,
        selectedRound, setSelectedRound,
        sessionType, setSessionType,
        isUplinkSyncing,
        uplinkNotice,
        triggerUplink
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
