import React, { useState } from 'react';
import {
  AppBar, Toolbar, Button, Avatar, Menu, MenuItem, Dialog,
  DialogTitle, DialogContent, IconButton, TextField, DialogActions,
  Typography, Box, Badge, Chip
} from '@mui/material';
import { styled, keyframes } from '@mui/system';
import { Link } from 'react-router-dom';
import AccountBoxIcon from '@mui/icons-material/AccountBox';
import SettingsIcon from '@mui/icons-material/Settings';
import LogoutIcon from '@mui/icons-material/Logout';
import CloseIcon from '@mui/icons-material/Close';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import databricksLogo from '../assets/icons/databricks.png';
import databricksIcon from '../assets/icons/databricks_small.png';
import user_pic from '../assets/icons/rodrigo.jpeg';
import Chatbot from './Chatbot';
import { useChatbot } from './ChatbotContext';

const pulse = keyframes`
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(255, 54, 33, 0.7);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(255, 54, 33, 0);
  }
`;

const StyledAppBar = styled(AppBar)(({ theme }) => ({
  backgroundColor: 'rgba(255, 255, 255, 0.95)',
  backdropFilter: 'blur(20px)',
  boxShadow: '0 2px 20px rgba(0,0,0,0.08)',
  borderBottom: '1px solid rgba(0,0,0,0.05)',
}));

const AIButton = styled(Button)(({ theme }) => ({
  backgroundColor: '#FF3621',
  color: 'white',
  fontWeight: 600,
  borderRadius: '12px',
  padding: '8px 20px',
  textTransform: 'none',
  boxShadow: '0 4px 12px rgba(255,54,33,0.3)',
  transition: 'all 0.3s ease',
  '&:hover': {
    backgroundColor: '#E02F1A',
    transform: 'translateY(-2px)',
    boxShadow: '0 6px 16px rgba(255,54,33,0.4)',
  },
  '&:active': {
    transform: 'translateY(0)',
  }
}));

const StyledAvatar = styled(Avatar)(({ theme }) => ({
  cursor: 'pointer',
  width: 40,
  height: 40,
  border: '2px solid #FF3621',
  transition: 'all 0.3s ease',
  '&:hover': {
    transform: 'scale(1.1)',
    animation: `${pulse} 2s infinite`,
  }
}));

const StyledMenuItem = styled(MenuItem)(({ theme }) => ({
  padding: '12px 20px',
  borderRadius: '8px',
  margin: '4px 8px',
  transition: 'all 0.2s ease',
  '&:hover': {
    backgroundColor: '#FFF8F6',
    transform: 'translateX(4px)',
  }
}));

const OnlineBadge = styled('div')(({ theme }) => ({
  width: 10,
  height: 10,
  backgroundColor: '#4CAF50',
  borderRadius: '50%',
  position: 'absolute',
  bottom: 2,
  right: 2,
  border: '2px solid white',
}));

function Header() {
  const { isOpen, openChatbotWithMessage, closeChatbot } = useChatbot();
  const [anchorEl, setAnchorEl] = useState(null);
  const [profileOpen, setProfileOpen] = useState(false);

  const toggleChatbot = () => {
    isOpen ? closeChatbot() : openChatbotWithMessage('');
  };

  const handleProfileMenuOpen = (event) => setAnchorEl(event.currentTarget);
  const handleProfileMenuClose = () => setAnchorEl(null);
  const openProfileDialog = () => {
    setProfileOpen(true);
    handleProfileMenuClose();
  };
  const closeProfileDialog = () => setProfileOpen(false);

  return (
    <>
      <StyledAppBar position="fixed">
        <Toolbar sx={{ padding: '8px 24px' }}>
          <Box display="flex" alignItems="center" gap={3} flexGrow={1}>
            <Link to="/" style={{ textDecoration: 'none' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', transition: 'transform 0.3s', '&:hover': { transform: 'scale(1.05)' } }}>
                <img src={databricksLogo} alt="Databricks" style={{ height: '50px' }} />
              </Box>
            </Link>
            
            <AIButton 
              onClick={toggleChatbot} 
              startIcon={<SmartToyIcon />}
              endIcon={isOpen && <Chip label="Active" size="small" sx={{ backgroundColor: 'rgba(255,255,255,0.3)', color: 'white', height: 20, fontSize: 10 }} />}
            >
              AI Assistant
            </AIButton>
          </Box>

          <Box display="flex" alignItems="center" gap={2}>
            <Chip 
              label="Online" 
              size="small" 
              sx={{ 
                backgroundColor: '#E8F5E9', 
                color: '#4CAF50',
                fontWeight: 600,
                fontSize: 11,
                '& .MuiChip-label': { padding: '0 10px' }
              }} 
            />
            <Box sx={{ position: 'relative' }}>
              <StyledAvatar
                alt="User"
                src={user_pic}
                onClick={handleProfileMenuOpen}
              />
              <OnlineBadge />
            </Box>
          </Box>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleProfileMenuClose}
            PaperProps={{
              sx: {
                marginTop: 1,
                borderRadius: '12px',
                boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
                minWidth: 200,
              }
            }}
          >
            <Box sx={{ padding: '12px 20px', borderBottom: '1px solid #f0f0f0' }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1B3139' }}>
                Rodrigo Oliveira
              </Typography>
              <Typography variant="caption" sx={{ color: '#777' }}>
                Solutions Architect
              </Typography>
            </Box>
            <StyledMenuItem onClick={openProfileDialog}>
              <AccountBoxIcon sx={{ marginRight: 1.5, color: '#FF3621', fontSize: 20 }} />
              <Typography variant="body2" sx={{ fontWeight: 600 }}>Profile</Typography>
            </StyledMenuItem>
            <StyledMenuItem onClick={handleProfileMenuClose}>
              <SettingsIcon sx={{ marginRight: 1.5, color: '#1B3139', fontSize: 20 }} />
              <Typography variant="body2" sx={{ fontWeight: 600 }}>Settings</Typography>
            </StyledMenuItem>
            <StyledMenuItem onClick={handleProfileMenuClose}>
              <LogoutIcon sx={{ marginRight: 1.5, color: '#777', fontSize: 20 }} />
              <Typography variant="body2" sx={{ fontWeight: 600 }}>Logout</Typography>
            </StyledMenuItem>
          </Menu>
        </Toolbar>
      </StyledAppBar>

      <Chatbot open={isOpen} onClose={closeChatbot} />

      <Dialog 
        open={profileOpen} 
        onClose={closeProfileDialog} 
        fullWidth 
        maxWidth="sm"
        PaperProps={{
          sx: {
            borderRadius: '16px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
          }
        }}
      >
        <DialogTitle sx={{ paddingBottom: 1 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Typography variant="h6" sx={{ fontWeight: 700 }}>Your Profile</Typography>
            <IconButton onClick={closeProfileDialog} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Box display="flex" flexDirection="column" alignItems="center" mb={3}>
            <Box sx={{ position: 'relative', marginBottom: 2 }}>
              <Avatar 
                src={user_pic} 
                alt="Rodrigo" 
                sx={{ width: 100, height: 100, border: '4px solid #FF3621' }} 
              />
              <OnlineBadge style={{ width: 14, height: 14, bottom: 4, right: 4 }} />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>Rodrigo Oliveira</Typography>
            <Chip 
              label="Solutions Architect" 
              size="small" 
              sx={{ marginTop: 1, backgroundColor: '#FFF8F6', color: '#FF3621', fontWeight: 600 }} 
            />
            <Typography variant="body2" color="textSecondary" sx={{ marginTop: 1 }}>
              rodrigo@genaigenius.org
            </Typography>
          </Box>
          <TextField
            margin="dense"
            label="Name"
            value="Rodrigo Oliveira"
            fullWidth
            variant="outlined"
            sx={{ marginBottom: 2 }}
            InputProps={{ style: { borderRadius: '10px' } }}
          />
          <TextField
            margin="dense"
            label="Email Address"
            value="rodrigo@genaigenius.org"
            type="email"
            fullWidth
            variant="outlined"
            InputProps={{ style: { borderRadius: '10px' } }}
          />
        </DialogContent>
        <DialogActions sx={{ padding: '16px 24px' }}>
          <Button 
            onClick={closeProfileDialog} 
            variant="contained"
            sx={{ 
              backgroundColor: '#FF3621',
              borderRadius: '8px',
              textTransform: 'none',
              fontWeight: 600,
              '&:hover': { backgroundColor: '#E02F1A' }
            }}
          >
            Save Changes
          </Button>
          <Button 
            onClick={closeProfileDialog} 
            variant="outlined"
            sx={{ 
              borderRadius: '8px',
              textTransform: 'none',
              fontWeight: 600
            }}
          >
            Cancel
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default Header;
