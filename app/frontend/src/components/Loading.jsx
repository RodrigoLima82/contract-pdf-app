import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { keyframes } from '@mui/system';

const pulse = keyframes`
  0% {
    transform: scale(0.95);
    opacity: 0.7;
  }
  50% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(0.95);
    opacity: 0.7;
  }
`;

function Loading({ message = "Carregando...", size = 40 }) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 4,
        animation: `${pulse} 2s ease-in-out infinite`,
      }}
    >
      <CircularProgress size={size} sx={{ color: '#FF3621' }} />
      <Typography
        variant="body2"
        sx={{ marginTop: 2, color: '#1B3139', fontWeight: 500 }}
      >
        {message}
      </Typography>
    </Box>
  );
}

export default Loading;

