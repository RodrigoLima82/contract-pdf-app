import React, { useState, useEffect, useRef } from "react";
import {
  Drawer, Box, TextField, IconButton, Typography, Paper, Avatar,
  Chip, Fade, CircularProgress, Tooltip
} from "@mui/material";
import MicRecorder from 'mic-recorder-to-mp3';
import MicIcon from '@mui/icons-material/Mic';
import SendIcon from '@mui/icons-material/Send';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import CloseIcon from '@mui/icons-material/Close';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import { keyframes, styled } from "@mui/system";
import { Link } from "react-router-dom";
import axios from "axios";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import user_pic from "../assets/icons/rodrigo.jpeg";
import databricks_small from "../assets/icons/databricks_small.png";
import { useChatbot } from './ChatbotContext';

const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const pulse = keyframes`
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
`;

const ChatHeader = styled(Box)(({ theme }) => ({
  background: 'linear-gradient(135deg, #FF3621 0%, #E02F1A 100%)',
  padding: '24px',
  color: 'white',
  position: 'relative',
  boxShadow: '0 4px 12px rgba(255,54,33,0.3)',
}));

const ChatContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  height: "calc(100vh - 160px)",
  backgroundColor: "#FAFAFA",
  position: 'relative',
}));

const ResizeHandle = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isResizing',
})(({ isResizing }) => ({
  position: 'absolute',
  right: 0,
  top: 0,
  bottom: 0,
  width: '8px',
  cursor: 'ew-resize',
  backgroundColor: isResizing ? 'rgba(255,54,33,0.3)' : 'transparent',
  zIndex: 10,
  transition: isResizing ? 'none' : 'background-color 0.2s ease',
  '&:hover': {
    backgroundColor: 'rgba(255,54,33,0.2)',
  },
  '&::before': {
    content: '""',
    position: 'absolute',
    right: '3px',
    top: '50%',
    transform: 'translateY(-50%)',
    width: '2px',
    height: isResizing ? '60px' : '40px',
    backgroundColor: isResizing ? '#FF3621' : 'rgba(255,54,33,0.3)',
    borderRadius: '2px',
    transition: 'all 0.2s ease',
  }
}));

const ChatMessages = styled(Box)(({ theme }) => ({
  flexGrow: 1,
  overflowY: "auto",
  padding: '24px',
  display: "flex",
  flexDirection: "column",
  gap: '16px',
  '&::-webkit-scrollbar': {
    width: '8px',
  },
  '&::-webkit-scrollbar-track': {
    background: '#f1f1f1',
  },
  '&::-webkit-scrollbar-thumb': {
    background: '#FF3621',
    borderRadius: '4px',
  },
}));

const MessageWrapper = styled(Box)(() => ({
  display: "flex",
  alignItems: "flex-start",
  gap: '12px',
  animation: `${fadeIn} 0.3s ease`,
}));

const MessageBubble = styled(Paper)(({ theme }) => ({
  padding: '16px',
  maxWidth: "70%",
  transition: 'all 0.2s ease',
  '& p': {
    margin: 0,
    lineHeight: 1.6,
  },
  '& code': {
    padding: '2px 6px',
    borderRadius: '4px',
    fontSize: '13px',
  }
}));

const MarkdownContent = styled('div')(({ fromUser }) => ({
  '& p': {
    margin: '0 0 8px 0',
    lineHeight: 1.6,
  },
  '& p:last-child': {
    marginBottom: 0,
  },
  '& h1, & h2, & h3, & h4, & h5, & h6': {
    margin: '12px 0 8px 0',
    fontWeight: 600,
  },
  '& h2': {
    fontSize: '1.3em',
    borderBottom: fromUser ? '2px solid rgba(255,255,255,0.3)' : '2px solid rgba(255,54,33,0.2)',
    paddingBottom: '4px',
  },
  '& ul, & ol': {
    margin: '8px 0',
    paddingLeft: '24px',
  },
  '& li': {
    margin: '4px 0',
  },
  '& code': {
    backgroundColor: fromUser ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.05)',
    padding: '2px 6px',
    borderRadius: '4px',
    fontSize: '0.9em',
    fontFamily: 'monospace',
  },
  '& pre': {
    backgroundColor: fromUser ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)',
    padding: '12px',
    borderRadius: '8px',
    overflow: 'auto',
    margin: '8px 0',
  },
  '& pre code': {
    backgroundColor: 'transparent',
    padding: 0,
  },
  '& table': {
    width: '100%',
    borderCollapse: 'collapse',
    margin: '12px 0',
    fontSize: '0.9em',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
    borderRadius: '8px',
    overflow: 'hidden',
  },
  '& thead': {
    backgroundColor: fromUser ? 'rgba(255,255,255,0.2)' : '#FF3621',
  },
  '& thead th': {
    padding: '12px',
    textAlign: 'left',
    fontWeight: 600,
    color: fromUser ? '#fff' : '#fff',
    borderBottom: '2px solid rgba(255,255,255,0.3)',
  },
  '& tbody tr': {
    backgroundColor: fromUser ? 'rgba(255,255,255,0.05)' : '#fff',
    transition: 'background-color 0.2s ease',
  },
  '& tbody tr:nth-of-type(even)': {
    backgroundColor: fromUser ? 'rgba(255,255,255,0.08)' : 'rgba(255,54,33,0.05)',
  },
  '& tbody tr:hover': {
    backgroundColor: fromUser ? 'rgba(255,255,255,0.15)' : 'rgba(255,54,33,0.1)',
  },
  '& tbody td': {
    padding: '12px',
    borderBottom: fromUser ? '1px solid rgba(255,255,255,0.1)' : '1px solid rgba(0,0,0,0.05)',
  },
  '& tbody tr:last-child td': {
    borderBottom: 'none',
  },
  '& strong': {
    fontWeight: 600,
    color: fromUser ? '#fff' : '#FF3621',
  },
  '& a': {
    color: fromUser ? '#fff' : '#FF3621',
    textDecoration: 'underline',
  },
  '& blockquote': {
    borderLeft: fromUser ? '4px solid rgba(255,255,255,0.3)' : '4px solid #FF3621',
    margin: '8px 0',
    paddingLeft: '12px',
    fontStyle: 'italic',
    color: fromUser ? 'rgba(255,255,255,0.9)' : 'rgba(0,0,0,0.7)',
  },
}));

const MessageInput = styled(Box)(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  gap: '12px',
  padding: '12px 24px',
  backgroundColor: "white",
  borderTop: '1px solid #E0E0E0',
  boxShadow: '0 -2px 12px rgba(0,0,0,0.05)',
}));

const StyledTextField = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    borderRadius: '12px',
    backgroundColor: '#F5F5F5',
    transition: 'all 0.2s ease',
    '& fieldset': {
      borderColor: 'transparent',
    },
    '&:hover': {
      backgroundColor: '#ECECEC',
      '& fieldset': {
        borderColor: '#FF3621',
      },
    },
    '&.Mui-focused': {
      backgroundColor: 'white',
      '& fieldset': {
        borderColor: '#FF3621',
        borderWidth: '2px',
      },
    },
  },
}));

const ActionButton = styled(IconButton)(({ theme, variant }) => ({
  width: 48,
  height: 48,
  borderRadius: '12px',
  transition: 'all 0.2s ease',
  ...(variant === 'send' && {
    backgroundColor: '#FF3621',
    color: 'white',
    '&:hover': {
      backgroundColor: '#E02F1A',
      transform: 'scale(1.05)',
    },
    '&:disabled': {
      backgroundColor: '#CCC',
      color: '#999',
    }
  }),
  ...(variant === 'clear' && {
    backgroundColor: '#F5F5F5',
    color: '#666',
    '&:hover': {
      backgroundColor: '#E0E0E0',
    },
  }),
  ...(variant === 'mic' && {
    backgroundColor: '#1B3139',
    color: 'white',
    '&:hover': {
      backgroundColor: '#0D1F27',
      animation: `${pulse} 0.5s ease`,
    },
  }),
}));

const StyledAvatar = styled(Avatar)(({ theme }) => ({
  width: 36,
  height: 36,
  boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
}));

const SuggestionChip = styled(Chip)(({ theme }) => ({
  padding: '12px',
  height: 'auto',
  borderRadius: '12px',
  backgroundColor: 'white',
  border: '2px dashed #FF3621',
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  marginBottom: '16px',
  '&:hover': {
    backgroundColor: '#FFF8F6',
    borderStyle: 'solid',
    transform: 'translateY(-2px)',
    boxShadow: '0 4px 12px rgba(255,54,33,0.2)',
  },
  '& .MuiChip-label': {
    display: 'block',
    whiteSpace: 'normal',
    padding: '8px 12px',
  }
}));

function Chatbot({ open, onClose }) {
  const { prefilledMessage, context, suggestion, setSuggestion, conversationId, setConversationId } = useChatbot();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState(prefilledMessage || "");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recorder, setRecorder] = useState(null);
  const [chatWidth, setChatWidth] = useState(() => {
    const saved = localStorage.getItem('chatWidth');
    return saved ? parseInt(saved, 10) : 900;
  });
  const [isResizing, setIsResizing] = useState(false);
  const resizeStartX = useRef(0);
  const startWidth = useRef(chatWidth);

  if (conversationId && conversationId.length === 0) {
    setConversationId("0")
  }

  useEffect(() => {
    setInput(prefilledMessage || "");
  }, [prefilledMessage]);

  // Save chat width to localStorage
  useEffect(() => {
    localStorage.setItem('chatWidth', chatWidth.toString());
  }, [chatWidth]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth"});
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Resize handlers
  const handleResizeStart = (e) => {
    setIsResizing(true);
    resizeStartX.current = e.clientX;
    startWidth.current = chatWidth;
    e.preventDefault();
  };

  useEffect(() => {
    const handleResizeMove = (e) => {
      if (!isResizing) return;
      
      // Para borda direita: arrastar para direita aumenta a largura
      const deltaX = e.clientX - resizeStartX.current;
      const newWidth = Math.max(500, Math.min(1400, startWidth.current + deltaX));
      setChatWidth(newWidth);
    };

    const handleResizeEnd = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleResizeMove);
      document.addEventListener('mouseup', handleResizeEnd);
      document.body.style.cursor = 'ew-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleResizeMove);
      document.removeEventListener('mouseup', handleResizeEnd);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, chatWidth]);

  const simulateStreamingResponse = (responseText, audio) => {
    const words = responseText.split(' ');
    let currentIndex = 0;
    let displayedText = "";
    const interval = 50;
  
    const streamInterval = setInterval(() => {
      if (currentIndex < words.length) {
        displayedText += (displayedText ? " " : "") + words[currentIndex];
        currentIndex += 1;
  
        if (!audio) {
          setMessages((prevMessages) => [
            ...prevMessages.slice(0, -1),
            { text: displayedText, fromUser: false },
          ]);
        } else {
          setMessages((prevMessages) => [
            ...prevMessages.slice(0, -1),
            { text: "🎤 " + displayedText, fromUser: true },
          ]);
        }
  
        if (currentIndex % 10 === 0 || currentIndex === words.length) {
          scrollToBottom();
        }
        
      } else {
        clearInterval(streamInterval);
        setLoading(false);
      }
    }, interval);
  };

  const AudioRecorder = () => {
    const startRecording = async () => {
      const newRecorder = new MicRecorder({ bitRate: 128 });
      
      if ("MediaRecorder" in window) {
        try {
          await navigator.mediaDevices.getUserMedia({ audio: true });
          setIsRecording(true);
          newRecorder.start();
          setRecorder(newRecorder);
        } catch (err) {
          alert("Por favor, permita acesso ao microfone.");
        }
      }
    };

    const stopRecording = async () => {
      if (recorder) {
        try {
          const [buffer, blob] = await recorder.stop().getMp3();
          const reader = new FileReader();
          
          reader.onloadend = async () => {
            const base64Audio = reader.result;
            try {
              setLoading(true);
              const response = await axios.post(`${process.env.REACT_APP_API_URL}/chat_audio/`, {
                audio: base64Audio,
                chat_history: messages.map((msg) => [msg.text, msg.fromUser ? "user" : "bot"])
              });
              
              const transcription = response.data.response;
              setMessages((prevMessages) => [
                ...prevMessages,
                { text: "", fromUser: true },
              ]);
              simulateStreamingResponse(transcription, true);
              
            } catch (error) {
              console.error("Error with audio:", error);
              setLoading(false);
            }
          };
          
          reader.readAsDataURL(blob);
          setIsRecording(false);
        } catch (e) {
          console.error("Failed to stop recording", e);
          setIsRecording(false);
        }
      }
    };

    return (
      <Tooltip title={isRecording ? "Parar gravação" : "Gravar áudio"}>
        <ActionButton 
          variant="mic"
          onClick={isRecording ? stopRecording : startRecording}
        >
          {isRecording ? <CircularProgress size={24} sx={{ color: 'white' }} /> : <MicIcon />}
        </ActionButton>
      </Tooltip>
    );
  };

  const handleSend = async () => {
    if (input.trim() === "") return;
    
    const newMessages = [...messages, { text: input, fromUser: true }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await axios.post(`${process.env.REACT_APP_API_URL}/chat/`, {
        text: input,
        chat_history: messages.map((msg) => [msg.text, msg.fromUser ? "user" : "bot"])
      });
  
      const botResponse = response.data.response;
      setMessages((prevMessages) => [
        ...prevMessages,
        { text: "", fromUser: false },
      ]);
  
      simulateStreamingResponse(botResponse, false);
    
    } catch (error) {
      console.error("Error sending message:", error);
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
    setSuggestion(null);
  };

  const handleSuggestionClick = () => {
    setInput(suggestion);
    setSuggestion("");
  };

  
  return (
    <Drawer 
      anchor="left" 
      open={open} 
      onClose={onClose}
      PaperProps={{
        sx: {
          width: chatWidth,
          transition: isResizing ? 'none' : 'width 0.2s ease',
        }
      }}
    >
      <ChatHeader>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <SmartToyIcon sx={{ fontSize: 40 }} />
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 800 }}>
                AI Assistant
              </Typography>
              <Link to="https://docs.databricks.com/en/generative-ai/generative-ai.html" style={{ textDecoration: 'none' }}>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.9)', fontWeight: 600 }}>
                  GenAI Powered by Databricks
                </Typography>
              </Link>
            </Box>
          </Box>
          <IconButton onClick={onClose} sx={{ color: 'white' }}>
            <CloseIcon />
          </IconButton>
        </Box>
        {context && (
          <Chip 
            label={`Usando ${context}`}
            icon={<SmartToyIcon style={{ color: 'white' }} />}
            sx={{ 
              backgroundColor: 'rgba(255,255,255,0.2)',
              color: 'white',
              fontWeight: 600,
              border: '1px solid rgba(255,255,255,0.3)'
            }}
          />
        )}
      </ChatHeader>

      <ChatContainer>
        <ResizeHandle isResizing={isResizing} onMouseDown={handleResizeStart} />
        <ChatMessages>
          {messages.length === 0 && (
            <Fade in={true}>
              <Box sx={{ textAlign: 'center', padding: 4, color: '#999' }}>
                <SmartToyIcon sx={{ fontSize: 64, marginBottom: 2, color: '#FF3621', opacity: 0.3 }} />
                <Typography variant="h6" sx={{ fontWeight: 600, color: '#666' }}>
                  Como posso ajudar?
                </Typography>
                <Typography variant="body2" sx={{ marginTop: 1 }}>
                  Faça perguntas sobre os dados dos PDFs extraídos
                </Typography>
              </Box>
            </Fade>
          )}

          {messages.map((message, index) => (
            <Box 
              key={index} 
              sx={{
                display: 'flex',
                flexDirection: message.fromUser ? 'row-reverse' : 'row',
                alignItems: 'flex-start',
                gap: '12px',
                animation: `${fadeIn} 0.3s ease`,
              }}
            >
              <StyledAvatar 
                src={message.fromUser ? user_pic : databricks_small} 
                alt={message.fromUser ? "User" : "AI"}
                sx={{
                  border: message.fromUser ? '2px solid #1B3139' : '2px solid #FF3621',
                }}
              />
              <Paper
                sx={{
                  padding: '16px',
                  backgroundColor: message.fromUser ? '#FF3621' : 'white',
                  color: message.fromUser ? 'white' : '#1B3139',
                  maxWidth: "70%",
                  borderRadius: message.fromUser ? "20px 20px 4px 20px" : "20px 20px 20px 4px",
                  boxShadow: message.fromUser 
                    ? '0 4px 12px rgba(255,54,33,0.3)'
                    : '0 2px 8px rgba(0,0,0,0.08)',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    boxShadow: message.fromUser 
                      ? '0 6px 16px rgba(255,54,33,0.4)'
                      : '0 4px 12px rgba(0,0,0,0.12)',
                  },
                }}
              >
                <MarkdownContent fromUser={message.fromUser}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.text}
                  </ReactMarkdown>
                </MarkdownContent>
              </Paper>
            </Box>
          ))}

          {loading && (
            <Box 
              sx={{
                display: 'flex',
                flexDirection: 'row',
                alignItems: 'flex-start',
                gap: '12px',
                animation: `${fadeIn} 0.3s ease`,
              }}
            >
              <StyledAvatar 
                src={databricks_small} 
                alt="AI"
                sx={{ border: '2px solid #FF3621' }}
              />
              <Paper
                sx={{
                  padding: '16px',
                  backgroundColor: 'white',
                  color: '#1B3139',
                  borderRadius: "20px 20px 20px 4px",
                  boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={16} sx={{ color: '#FF3621' }} />
                  <Typography variant="body2">Pensando...</Typography>
                </Box>
              </Paper>
            </Box>
          )}

          <div ref={messagesEndRef} />
        </ChatMessages>

        {suggestion && (
          <Box sx={{ padding: '0 24px' }}>
            <SuggestionChip
              label={
                <Box>
                  <Typography variant="caption" sx={{ fontWeight: 700, color: '#FF3621', display: 'block', marginBottom: 0.5 }}>
                    💡 Sugestão:
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#333' }}>
                    {suggestion}
                  </Typography>
                </Box>
              }
              onClick={handleSuggestionClick}
            />
          </Box>
        )}

        <MessageInput>
          <StyledTextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="Digite sua mensagem..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            disabled={loading}
          />
          
          <Tooltip title="Enviar mensagem">
            <span>
              <ActionButton 
                variant="send"
                onClick={handleSend}
                disabled={!input.trim() || loading}
              >
                <SendIcon />
              </ActionButton>
            </span>
          </Tooltip>

          <Tooltip title="Limpar conversa">
            <span>
              <ActionButton 
                variant="clear"
                onClick={handleClear}
                disabled={messages.length === 0}
              >
                <DeleteOutlineIcon />
              </ActionButton>
            </span>
          </Tooltip>

          <AudioRecorder />
        </MessageInput>
      </ChatContainer>
    </Drawer>
  );
}

export default Chatbot;
