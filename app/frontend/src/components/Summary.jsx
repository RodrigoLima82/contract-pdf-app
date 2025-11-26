import React from "react";
import { Typography, Box, Avatar, Card, Grid, Chip } from '@mui/material';
import { styled, keyframes } from '@mui/system';
import ArticleIcon from '@mui/icons-material/Article';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import SpeedIcon from '@mui/icons-material/Speed';
import SecurityIcon from '@mui/icons-material/Security';

const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const float = keyframes`
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
`;

const StyledCard = styled(Card)(({ theme }) => ({
  marginTop: 16,
  borderRadius: '20px',
  background: 'linear-gradient(135deg, #FF3621 0%, #E02F1A 100%)',
  boxShadow: '0 8px 32px rgba(255,54,33,0.3)',
  color: 'white',
  overflow: 'hidden',
  position: 'relative',
  animation: `${fadeInUp} 0.8s ease-out`,
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'radial-gradient(circle at top right, rgba(255,255,255,0.1), transparent 60%)',
  }
}));

const FloatingIconBox = styled(Box)(({ theme }) => ({
  width: 100,
  height: 100,
  borderRadius: '20px',
  backgroundColor: 'white',
  boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
  border: '4px solid white',
  animation: `${float} 3s ease-in-out infinite`,
  transition: 'transform 0.3s ease',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  '&:hover': {
    transform: 'scale(1.1) rotate(5deg)',
  }
}));

const FeatureChip = styled(Chip)(({ theme }) => ({
  backgroundColor: 'rgba(255,255,255,0.2)',
  color: 'white',
  fontWeight: 600,
  backdropFilter: 'blur(10px)',
  border: '1px solid rgba(255,255,255,0.3)',
  transition: 'all 0.3s ease',
  '&:hover': {
    backgroundColor: 'rgba(255,255,255,0.3)',
    transform: 'translateY(-2px)',
  }
}));

function Summary() {
  return (
    <StyledCard>
      <Box sx={{ padding: 4, position: 'relative', zIndex: 1 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={3} sx={{ display: 'flex', justifyContent: 'center' }}>
            <FloatingIconBox>
              <ArticleIcon sx={{ fontSize: 60, color: '#FF3621' }} />
            </FloatingIconBox>
          </Grid>

          <Grid item xs={12} md={6}>
            <Box textAlign={{ xs: 'center', md: 'left' }}>
              <Typography 
                variant="h3" 
                sx={{ 
                  fontWeight: 800,
                  marginBottom: 1,
                  textShadow: '0 2px 10px rgba(0,0,0,0.1)',
                  fontSize: { xs: '1.75rem', md: '2.5rem' }
                }}
              >
                Extração de Contratos com IA
              </Typography>
              <Typography 
                variant="h6" 
                sx={{ 
                  fontWeight: 400,
                  opacity: 0.95,
                  marginBottom: 2,
                  fontSize: { xs: '1rem', md: '1.25rem' }
                }}
              >
                Análise Automatizada de Contratos
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: { xs: 'center', md: 'flex-start' } }}>
                <FeatureChip 
                  icon={<AutoAwesomeIcon style={{ color: 'white' }} />} 
                  label="Powered by AI" 
                  size="small" 
                />
                <FeatureChip 
                  icon={<SpeedIcon style={{ color: 'white' }} />} 
                  label="Processamento Rápido" 
                  size="small" 
                />
                <FeatureChip 
                  icon={<SecurityIcon style={{ color: 'white' }} />} 
                  label="Databricks Secure" 
                  size="small" 
                />
              </Box>
            </Box>
          </Grid>

          <Grid item xs={12} md={3}>
            <Box 
              sx={{ 
                textAlign: 'center',
                backgroundColor: 'rgba(255,255,255,0.15)',
                backdropFilter: 'blur(10px)',
                padding: 3,
                borderRadius: '16px',
                border: '1px solid rgba(255,255,255,0.2)',
              }}
            >
              <Typography variant="h4" sx={{ fontWeight: 800, marginBottom: 0.5 }}>
                100%
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9, fontWeight: 500 }}>
                Automatizado
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </StyledCard>
  );
}

export default Summary;
