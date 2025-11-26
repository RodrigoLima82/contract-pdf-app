import React, { useState, useEffect } from 'react';
import { Card, CardContent, Box, Typography, Chip, CircularProgress } from '@mui/material';
import { styled, keyframes } from '@mui/system';
import DashboardIcon from '@mui/icons-material/Dashboard';
import api from '../utils/api';

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
  marginTop: '24px',
  borderRadius: '16px',
  boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
  overflow: 'hidden',
  animation: `${fadeIn} 0.6s ease-out`,
  transition: 'all 0.3s ease',
  '&:hover': {
    boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
  }
}));

const HeaderBox = styled(Box)(({ theme }) => ({
  background: 'linear-gradient(135deg, #1B3139 0%, #2C4A56 100%)',
  padding: '20px 24px',
  color: 'white',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
}));

const IframeContainer = styled(Box)(({ theme }) => ({
  position: 'relative',
  width: '100%',
  height: '600px',
  backgroundColor: '#F5F5F5',
}));

function PDFDashboard() {
  const [dashboardUrl, setDashboardUrl] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch dashboard URL from backend config
    const fetchConfig = async () => {
      try {
        const response = await api.get('/api/config');
        setDashboardUrl(response.data.dashboard_url);
      } catch (error) {
        console.error('Error fetching config:', error);
        // Fallback to environment variable if available
        setDashboardUrl(process.env.REACT_APP_DASHBOARD_URL || '');
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();
  }, []);

  return (
    <StyledCard>
      <HeaderBox>
        <Box display="flex" alignItems="center" gap={2}>
          <DashboardIcon sx={{ fontSize: 32 }} />
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Dashboard de Contratos
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.9 }}>
              Análise visual dos contratos processados
            </Typography>
          </Box>
        </Box>
        <Chip 
          label="Live Data" 
          size="small"
          sx={{ 
            backgroundColor: 'rgba(76,175,80,0.2)', 
            color: '#4CAF50',
            fontWeight: 600,
            border: '1px solid rgba(76,175,80,0.3)'
          }} 
        />
      </HeaderBox>
      
      <CardContent sx={{ padding: 0 }}>
        <IframeContainer>
          {loading ? (
            <Box display="flex" justifyContent="center" alignItems="center" height="100%">
              <CircularProgress />
            </Box>
          ) : dashboardUrl ? (
            <iframe
              src={dashboardUrl}
              width="100%"
              height="600"
              frameBorder="0"
              title="Databricks Dashboard"
            />
          ) : (
            <Box display="flex" justifyContent="center" alignItems="center" height="100%" flexDirection="column" gap={2}>
              <Typography variant="h6" color="text.secondary">
                Dashboard não configurado
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Configure REACT_APP_DASHBOARD_URL nas variáveis de ambiente
              </Typography>
            </Box>
          )}
        </IframeContainer>
      </CardContent>
    </StyledCard>
  );
}

export default PDFDashboard;
