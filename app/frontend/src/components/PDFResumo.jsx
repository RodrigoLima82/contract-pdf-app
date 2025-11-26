import React, { useEffect, useState } from 'react';
import { Container, Typography, Card, CardContent, Box, Avatar, Skeleton, Chip } from '@mui/material';
import { styled, keyframes } from '@mui/system';
import { useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import databricksLogo from '../assets/icons/databricks_small.png';
import DescriptionIcon from '@mui/icons-material/Description';
import api from "../utils/api";
import Loading from './Loading';

const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const StyledCard = styled(Card)(({ theme }) => ({
  borderRadius: '16px',
  boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
  marginBottom: '24px',
  animation: `${fadeIn} 0.6s ease-out`,
  transition: 'transform 0.3s ease',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
  }
}));

const GradientBox = styled(Box)(({ theme }) => ({
  background: 'linear-gradient(135deg, #FF3621 0%, #E02F1A 100%)',
  padding: '24px',
  borderRadius: '16px',
  display: 'flex',
  alignItems: 'center',
  marginBottom: '24px',
  boxShadow: '0 8px 24px rgba(255,54,33,0.3)',
  color: 'white',
  animation: `${fadeIn} 0.8s ease-out`,
}));

const MarkdownContent = styled(Box)(({ theme }) => ({
  fontSize: '15px',
  lineHeight: '1.8',
  color: '#333',
  '& h1, & h2, & h3': {
    color: '#1B3139',
    marginTop: '24px',
    marginBottom: '12px',
    fontWeight: 700,
  },
  '& h1': { fontSize: '24px' },
  '& h2': { fontSize: '20px' },
  '& h3': { fontSize: '18px' },
  '& p': {
    marginBottom: '16px',
  },
  '& ul, & ol': {
    paddingLeft: '24px',
    marginBottom: '16px',
  },
  '& li': {
    marginBottom: '8px',
  },
  '& strong': {
    color: '#FF3621',
    fontWeight: 700,
  },
  '& code': {
    backgroundColor: '#F5F5F5',
    padding: '2px 6px',
    borderRadius: '4px',
    fontSize: '14px',
  }
}));

function PDFDetail() {
  const { pdf } = useParams();
  const [markdownContent, setMarkdownContent] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.get("/api/summarize", {
          params: { pdf: pdf }
        });
        setMarkdownContent(response.data);
      } catch (error) {
        console.error("Error summarize:", error);
        setMarkdownContent("💥 Erro ao carregar resumo do PDF. Tente novamente mais tarde.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [pdf]);

  return (
    <Container sx={{ marginTop: 12, maxWidth: '900px !important' }}>
      <GradientBox>
        <DescriptionIcon sx={{ fontSize: 48, marginRight: 2 }} />
        <Box flexGrow={1}>
          <Typography variant="h4" sx={{ fontWeight: 800, marginBottom: 0.5 }}>
            Resumo do Contrato
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9 }}>
            {pdf}
          </Typography>
        </Box>
        <Chip 
          label="AI Generated" 
          sx={{ 
            backgroundColor: 'rgba(255,255,255,0.2)', 
            color: 'white',
            fontWeight: 600,
            border: '1px solid rgba(255,255,255,0.3)'
          }} 
        />
      </GradientBox>

      <StyledCard>
        <CardContent sx={{ padding: '32px' }}>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            marginBottom: 3,
            paddingBottom: 2,
            borderBottom: '2px solid #F5F5F5'
          }}>
            <Avatar 
              src={databricksLogo} 
              alt="Databricks" 
              sx={{ marginRight: 2, width: 40, height: 40 }} 
            />
            <Box>
              <Typography variant="h6" sx={{ color: '#1B3139', fontWeight: 700 }}>
                Resumo Gerado por IA
              </Typography>
              <Typography variant="caption" sx={{ color: '#777' }}>
                Powered by Databricks AI
              </Typography>
            </Box>
          </Box>

          {loading ? (
            <Box>
              <Skeleton variant="text" width="100%" height={30} sx={{ marginBottom: 2 }} />
              <Skeleton variant="text" width="90%" height={30} sx={{ marginBottom: 2 }} />
              <Skeleton variant="text" width="95%" height={30} sx={{ marginBottom: 2 }} />
              <Skeleton variant="rectangular" width="100%" height={200} sx={{ borderRadius: '8px' }} />
            </Box>
          ) : (
            <MarkdownContent>
              <ReactMarkdown>{markdownContent}</ReactMarkdown>
            </MarkdownContent>
          )}
        </CardContent>
      </StyledCard>
    </Container>
  );
}

export default PDFDetail;
