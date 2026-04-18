import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import InputBox from './InputBox';
import WelcomeScreen from './WelcomeScreen';
import '../styles/global.css';

const ChatArea = ({ messages, onSend, onSuggestionClick, isLoading, loadingMessages }) => {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (loadingMessages) {
    return (
      <div className="chat-area">
        <div className="messages-loading">
          <div className="loading-spinner"></div>
          <p>加载消息中...</p>
        </div>
        <InputBox onSend={onSend} disabled={true} />
      </div>
    );
  }

  return (
    <div className="chat-area">
      {messages.length === 0 ? (
        <WelcomeScreen onSuggestionClick={onSuggestionClick} />
      ) : (
        <div className="messages-container">
          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}
          {isLoading && (
            <div className="message-bubble assistant">
              <div className="message-avatar">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-color)" strokeWidth="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                  <path d="M2 17l10 5 10-5"></path>
                  <path d="M2 12l10 5 10-5"></path>
                </svg>
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}
      <InputBox onSend={onSend} disabled={isLoading} />
    </div>
  );
};

export default ChatArea;
