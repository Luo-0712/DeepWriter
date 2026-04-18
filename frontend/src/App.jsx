import { useState, useEffect, useRef, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import { getSessions, createSession, getMessages, sendMessage, sendStreamMessage, deleteSession } from './utils/api';
import './styles/global.css';

function App() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [loadedSessions, setLoadedSessions] = useState(new Set());
  const [loadingSessionId, setLoadingSessionId] = useState(null);
  const activeSSESource = useRef(null);
  const currentSessionUuid = useRef(null);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    if (activeSession && !loadedSessions.has(activeSession.id)) {
      setLoadingSessionId(activeSession.id);
      loadMessages(activeSession.id);
    }
    currentSessionUuid.current = activeSession?.id || null;
    return () => {
      if (activeSSESource.current) {
        activeSSESource.current.close();
        activeSSESource.current = null;
      }
    };
  }, [activeSession?.id]);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const data = await getSessions();
      const sessionList = data.items.map(item => ({
        id: item.id,
        title: item.title,
        messages: [],
        status: item.status,
        createdAt: item.created_at,
        updatedAt: item.updated_at,
      }));
      setSessions(sessionList);
      if (sessionList.length > 0) {
        setActiveSession(sessionList[0]);
      }
    } catch (error) {
      console.error('加载会话失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (sessionId) => {
    try {
      setLoadingMessages(true);
      const data = await getMessages(sessionId);
      const messages = data.items.map(item => ({
        id: item.id,
        role: item.role,
        content: item.content,
        timestamp: item.created_at,
      }));
      setSessions(prev => {
        const updated = prev.map(s => 
          s.id === sessionId ? { ...s, messages } : s
        );
        setActiveSession(updated.find(s => s.id === sessionId));
        return updated;
      });
      setLoadedSessions(prev => new Set([...prev, sessionId]));
    } catch (error) {
      console.error('加载消息失败:', error);
    } finally {
      setLoadingMessages(false);
      setLoadingSessionId(null);
    }
  };

  const handleSend = async (content, session) => {
    const currentSession = session || activeSession;
    if (!currentSession) return;

    const newMessage = { role: 'user', content, timestamp: new Date() };
    
    setSessions(prev => {
      const updated = prev.map(s => 
        s.id === currentSession.id 
          ? { ...s, messages: [...s.messages, newMessage] }
          : s
      );
      setActiveSession(updated.find(s => s.id === currentSession.id));
      return updated;
    });
    
    setIsLoading(true);

    let assistantContent = '';
    const assistantMessageId = Date.now();
    
    setSessions(prev => {
      const updated = prev.map(s => 
        s.id === currentSession.id 
          ? { ...s, messages: [...s.messages, { id: assistantMessageId, role: 'assistant', content: '', timestamp: new Date() }] }
          : s
      );
      setActiveSession(updated.find(s => s.id === currentSession.id));
      return updated;
    });

    const eventSource = sendStreamMessage(
      currentSession.id,
      content,
      (chunk) => {
        assistantContent += chunk;
        setSessions(prev => {
          const updated = prev.map(s => 
            s.id === currentSession.id 
              ? { 
                  ...s, 
                  messages: s.messages.map(m => 
                    m.id === assistantMessageId 
                      ? { ...m, content: assistantContent }
                      : m
                  )
                }
              : s
          );
          setActiveSession(updated.find(s => s.id === currentSession.id));
          return updated;
        });
      },
      () => {
        setLoadedSessions(prev => new Set([...prev, currentSession.id]));
        setIsLoading(false);
        eventSource.close();
        activeSSESource.current = null;
      },
      (error) => {
        console.error('发送消息失败:', error);
        const errorMessage = { role: 'assistant', content: '抱歉，发生了错误。请稍后重试。', timestamp: new Date() };
        setSessions(prev => {
          const updated = prev.map(s => 
            s.id === currentSession.id 
              ? { ...s, messages: [...s.messages, errorMessage] }
              : s
          );
          setActiveSession(updated.find(s => s.id === currentSession.id));
          return updated;
        });
        setIsLoading(false);
        eventSource.close();
        activeSSESource.current = null;
      }
    );

    activeSSESource.current = eventSource;
  };

  const handleSelectSession = (session) => {
    if (activeSSESource.current) {
      activeSSESource.current.close();
      activeSSESource.current = null;
    }
    currentSessionUuid.current = session.id;
    setActiveSession(session);
  };

  const handleNewChat = async () => {
    try {
      const data = await createSession();
      const newSession = {
        id: data.id,
        title: data.title,
        messages: [],
        status: data.status,
        createdAt: data.created_at,
        updatedAt: data.updated_at,
      };
      setSessions(prev => [newSession, ...prev]);
      
      if (activeSSESource.current) {
        activeSSESource.current.close();
        activeSSESource.current = null;
      }
      currentSessionUuid.current = newSession.id;
      setActiveSession(newSession);
    } catch (error) {
      console.error('创建会话失败:', error);
    }
  };

  const handleDeleteSession = async (session) => {
    try {
      await deleteSession(session.id);
      
      const isDeletingActive = activeSession?.id === session.id;
      
      setSessions(prev => {
        const remaining = prev.filter(s => s.id !== session.id);
        return remaining;
      });

      setLoadedSessions(prev => {
        const newSet = new Set(prev);
        newSet.delete(session.id);
        return newSet;
      });
      
      if (isDeletingActive) {
        setTimeout(() => {
          setSessions(prev => {
            const firstSession = prev.length > 0 ? prev[0] : null;
            setActiveSession(firstSession);
            return prev;
          });
        }, 50);
      }
    } catch (error) {
      console.error('删除会话失败:', error);
    }
  };

  const handleSuggestionClick = async (text) => {
    let currentSession = activeSession;
    if (!currentSession) {
      const data = await createSession();
      currentSession = {
        id: data.id,
        title: data.title,
        messages: [],
        status: data.status,
        createdAt: data.created_at,
        updatedAt: data.updated_at,
      };
      setSessions(prev => [currentSession, ...prev]);
      setActiveSession(currentSession);
      currentSessionUuid.current = currentSession.id;
    }
    handleSend(text, currentSession);
  };

  if (loading) {
    return (
      <div className="app-container">
        <div className="loading-screen">
          <div className="loading-spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Sidebar
        sessions={sessions}
        activeSession={activeSession}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
      />
      <main className="main-content">
        <ChatArea
          messages={activeSession?.messages || []}
          onSend={handleSend}
          onSuggestionClick={handleSuggestionClick}
          isLoading={isLoading}
          loadingMessages={loadingMessages}
          isSessionLoading={activeSession?.id === loadingSessionId}
        />
      </main>
    </div>
  );
}

export default App;
