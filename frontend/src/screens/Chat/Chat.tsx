import React, { useState, useRef, useEffect } from 'react';
import '../../components/Layout.css';
import './Chat.css';
import { chatWithML } from '@/utils/mlApi';
import { saveChatMessage, getCurrentUserId, getChatHistory, deleteChatHistory } from '@/utils/api';

interface Message {
  sender: 'user' | 'llm';
  text: string;
}

export const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [userId, setUserId] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    getCurrentUserId().then(async (id) => {
      console.log('getCurrentUserId result:', id);
      setUserId(id);
      if (id) {
        console.log('Loading chat history for user:', id);
        try {
          const res = await getChatHistory(id);
          console.log('getChatHistory response status:', res.status);
          if (res.ok) {
            const history = await res.json();
            console.log('Chat history loaded:', history);
            setMessages(
              history.map((m: any) => ({ sender: m.role === 'user' ? 'user' : 'llm', text: m.content }))
            );
          } else {
            const error = await res.text();
            console.error('Failed to load chat history:', error);
          }
        } catch (error) {
          console.error('Error loading chat history:', error);
        }
      } else {
        console.warn('No user ID available, using mock user ID for testing');
        setUserId('test-user-123');
      }
    });
  }, []);

  const sendMessage = async () => {
    console.log('sendMessage called with:', { input: input.trim(), userId });
    if (!input.trim()) {
      console.error('Input is empty');
      return;
    }
    if (!userId) {
      console.error('User ID is not available');
      return;
    }

    const userMessage: Message = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    const inputText = input;
    setInput('');

    console.log('Saving user message to history...');
    try {
      const saveRes = await saveChatMessage(userId, 'user', inputText);
      console.log('Save user message response status:', saveRes.status);
      if (!saveRes.ok) {
        const err = await saveRes.text();
        console.error('Error saving user message:', err);
      }
    } catch (e) {
      console.error('Error calling saveChatMessage (user):', e);
    }

    try {
      const chatHistory = [
        ...messages,
        userMessage
      ].map((m) => ({ role: m.sender === 'user' ? 'user' : 'llm', content: m.text }));

      console.log('Sending chat history to ML:', chatHistory.length, 'messages');
      const result = await chatWithML(userMessage.text, chatHistory);
      const llmResponse = result.response ?? 'No response from ML service.';

      let parsedResponse;
      try {
        parsedResponse = JSON.parse(llmResponse);
      } catch (e) {
        console.error('Failed to parse ML response as JSON:', e);
        parsedResponse = null;
      }

      let displayMessage;
      if (parsedResponse) {
        switch (parsedResponse.status) {
          case 'added':
            displayMessage = 'Task successfully added to the calendar!';
            break;
          case 'deleted':
            displayMessage = 'Task successfully deleted from the calendar!';
            break;
          case 'changed':
            displayMessage = 'Task successfully updated in the calendar!';
            break;
          default:
            displayMessage = parsedResponse.data ?? 'Invalid response from ML service.';
        }
      } else {
        displayMessage = llmResponse;
      }

      setMessages((prev) => [
        ...prev,
        { sender: 'llm', text: displayMessage }
      ]);

      try {
        const saveRes = await saveChatMessage(userId, 'llm', displayMessage);
        if (!saveRes.ok) {
          const err = await saveRes.text();
          console.error('Error saving llm message:', err);
        }
      } catch (e) {
        console.error('Error calling saveChatMessage (llm):', e);
      }
    } catch (error) {
      console.error('Error connecting to ML service:', error);
      const errorMessage = 'Error: Unable to connect to ML service';
      setMessages((prev) => [
        ...prev,
        { sender: 'llm', text: errorMessage }
      ]);
      try {
        const saveRes = await saveChatMessage(userId, 'llm', errorMessage);
        if (!saveRes.ok) {
          const err = await saveRes.text();
          console.error('Error saving llm error message:', err);
        }
      } catch (e) {
        console.error('Error calling saveChatMessage (llm error):', e);
      }
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const deleteChatMessages = async () => {
    if (!userId) {
      console.error('User ID is not available');
      return;
    }

    if (!window.confirm('Are you sure you want to delete all chat messages? This action cannot be undone.')) {
      return;
    }

    try {
      console.log('Deleting chat messages for user:', userId);
      const response = await deleteChatHistory(userId);

      if (response.ok) {
        console.log('Chat messages deleted successfully');
        setMessages([]);
      } else {
        const error = await response.text();
        console.error('Failed to delete chat messages:', error);
        alert('Failed to delete chat messages. Please try again.');
      }
    } catch (error) {
      console.error('Error deleting chat messages:', error);
      alert('Error deleting chat messages. Please try again.');
    }
  };

  return (
    <div className="chat-container">
      {messages.length === 0 ? (
        <div className="chat-welcome">
          <div className="welcome-text">
            <h1 className="greeting">HI USER</h1>
            <h2 className="question">WHAT WOULD LIKE TO DISCUSS TODAY?</h2>
          </div>
        </div>
      ) : (
        <div className="chat-messages">
          {messages.map((msg, idx) => (
            <div
              key={`${msg.sender}-${idx}`}
              className={`chat-message ${msg.sender === 'user' ? 'user' : 'llm'}`}
            >
              <div className="chat-message-content">
                {msg.text}
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
      )}
      <div className="chat-input-section">
        <div className="chat-input-container">
          <div className="input-branding">
            <span className="input-brand-text">EGO:<span className="input-brand-highlight">AI</span></span>
          </div>
          <div className="chat-input-wrapper">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleInputKeyDown}
              placeholder="Message EGO:AI..."
              className="chat-input"
            />
            <div className="chat-button-group">
              <button className="chat-mic-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M12 15C13.66 15 15 13.66 15 12V6C15 4.34 13.66 3 12 3C10.34 3 9 4.34 9 6V12C9 13.66 10.34 15 12 15Z" fill="currentColor"/>
                  <path d="M19 12C19 15.53 16.39 18.44 13 18.93V21H11V18.93C7.61 18.44 5 15.53 5 12H7C7 14.76 9.24 17 12 17C14.76 17 17 14.76 17 12H19Z" fill="currentColor"/>
                </svg>
              </button>
              <button 
                onClick={sendMessage} 
                className="chat-send-btn"
                disabled={!input.trim()}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M2.01 21L23 12L2.01 3L2 10L17 12L2 14L2.01 21Z" fill="currentColor"/>
                </svg>
              </button>
            </div>
          </div>
          {messages.length > 0 && (
            <button 
              onClick={deleteChatMessages}
              className="chat-delete-btn"
              title="Delete all chat messages"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M19 7L18.1327 19.1425C18.0579 20.1891 17.187 21 16.1378 21H7.86224C6.81296 21 5.94208 20.1891 5.86732 19.1425L5 7M10 11V17M14 11V17M15 7V4C15 3.44772 14.5523 3 14 3H10C9.44772 3 9 3.44772 9 4V7M4 7H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
