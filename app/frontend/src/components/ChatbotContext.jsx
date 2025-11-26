import React, { createContext, useContext, useState } from 'react';

const ChatbotContext = createContext();

export const ChatbotProvider = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [prefilledMessage, setPrefilledMessage] = useState("");
  const [context, setContext] = useState("");
  const [suggestion, setSuggestion] = useState(null);  // New state for suggestion
  const [conversationId, setConversationId] = useState("0");  // New state for conversation ID

  const openChatbotWithMessage = (conversationId, message, context) => {
    setConversationId(conversationId);
    setPrefilledMessage(message);
    setContext(context);
    setIsOpen(true);
  };

  const openChatbotWithSuggestion = (conversationId, message, context) => {
    setConversationId(conversationId);
    setSuggestion(message);
    setContext(context);
    setIsOpen(true);
  };  

  const closeChatbot = () => {
    setIsOpen(false);
    setPrefilledMessage("");
    setContext("");
    setSuggestion(null);  // Reset suggestion on close
  };

  return (
    <ChatbotContext.Provider value={{ isOpen, openChatbotWithMessage, closeChatbot, prefilledMessage, context, suggestion, setSuggestion, openChatbotWithSuggestion, conversationId, setConversationId }}>
      {children}
    </ChatbotContext.Provider>
  );
};

export const useChatbot = () => {
  return useContext(ChatbotContext);
};