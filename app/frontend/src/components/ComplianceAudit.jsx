import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card, CardContent, Box, Typography, Chip, Container,
  Button, IconButton, TextField, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Snackbar, Alert as MuiAlert,
} from '@mui/material';
import { styled, keyframes } from '@mui/system';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import api from '../utils/api';
import TableSkeleton from './TableSkeleton';
import EmptyState from './EmptyState';

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
  animation: `${fadeIn} 0.6s ease-out`,
  marginTop: '24px',
}));

const HeaderBox = styled(Box)(({ theme }) => ({
  background: 'linear-gradient(135deg, #1B3139 0%, #2C4A56 100%)',
  padding: '24px 32px',
  borderRadius: '16px',
  marginBottom: '24px',
  color: 'white',
  boxShadow: '0 8px 24px rgba(27,49,57,0.3)',
  animation: `${fadeIn} 0.8s ease-out`,
}));

const HeaderTableCell = styled(TableCell)(({ theme }) => ({
  fontWeight: 700,
  backgroundColor: '#1B3139',
  color: 'white',
  fontSize: 13,
  padding: '16px',
}));

const BodyTableCell = styled(TableCell)(({ theme }) => ({
  fontSize: 13,
  color: '#555',
  padding: '16px',
  verticalAlign: 'middle',
}));

function getAuditButtonSx(auditorStatus, isOkButton) {
  const selected = isOkButton
    ? auditorStatus === 'Compliance'
    : auditorStatus === 'Não Compliance';
  return {
    textTransform: 'none',
    fontWeight: 600,
    minWidth: 100,
    ...(selected && isOkButton && {
      backgroundColor: '#2E7D32',
      color: 'white',
      '&:hover': { backgroundColor: '#1B5E20' },
    }),
    ...(selected && !isOkButton && {
      backgroundColor: '#C62828',
      color: 'white',
      '&:hover': { backgroundColor: '#B71C1C' },
    }),
    ...(!selected && {
      borderColor: '#ddd',
      color: '#666',
      '&:hover': { borderColor: '#999', backgroundColor: 'rgba(0,0,0,0.04)' },
    }),
  };
}

function ComplianceAudit() {
  const { pdf } = useParams();
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(null); // key: `${path}|${template_name}|${item_description}`
  const [notes, setNotes] = useState({}); // key -> value
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  const showNotification = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const fetchCompliance = async () => {
    try {
      const response = await api.get('/api/compliance', { params: { pdf } });
      setItems(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error fetching compliance:', error);
      setItems([]);
      showNotification('Erro ao carregar itens de compliance.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompliance();
  }, [pdf]);

  useEffect(() => {
    const initial = {};
    items.forEach((row) => {
      const key = `${row.path}|${row.template_name}|${row.item_description}`;
      if (row.auditor_notes) initial[key] = row.auditor_notes;
    });
    setNotes((prev) => ({ ...initial, ...prev }));
  }, [items.length]);

  const handleSetAudit = async (row, auditorStatus) => {
    const key = `${row.path}|${row.template_name}|${row.item_description}`;
    setSaving(key);
    try {
      await api.patch('/api/compliance/audit', {
        path: row.path,
        template_name: row.template_name,
        item_description: row.item_description,
        auditor_status: auditorStatus,
        auditor_notes: notes[key] || null,
      });
      showNotification('Parecer salvo.', 'success');
      await fetchCompliance();
      // Defer state updates to next frame to avoid ResizeObserver loop (MUI table re-render)
      requestAnimationFrame(() => {
        setNotes((prev) => {
          const next = { ...prev };
          delete next[key];
          return next;
        });
        setSaving(null);
      });
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Erro ao salvar parecer.', 'error');
      setSaving(null);
    }
  };

  const handleNotesChange = (key, value) => {
    setNotes((prev) => ({ ...prev, [key]: value }));
  };

  // Não Compliance primeiro, depois Compliance; mantém a ordem original em cada grupo
  const sortedItems = React.useMemo(() => {
    const naoCompliance = items.filter((row) => row.status === 'Não Compliance');
    const compliance = items.filter((row) => row.status !== 'Não Compliance');
    return [...naoCompliance, ...compliance];
  }, [items]);

  return (
    <Container sx={{ marginTop: 12, maxWidth: '1400px !important' }}>
      <HeaderBox>
        <Box display="flex" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={2}>
          <Box display="flex" alignItems="center" gap={2}>
            <IconButton onClick={() => navigate(-1)} sx={{ color: 'white' }} size="small">
              <ArrowBackIcon />
            </IconButton>
            <FactCheckIcon sx={{ fontSize: 40 }} />
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 800, marginBottom: 0.5 }}>
                Auditoria de Compliance
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                {decodeURIComponent(pdf || '')}
              </Typography>
            </Box>
          </Box>
        </Box>
      </HeaderBox>

      <StyledCard>
        <CardContent sx={{ padding: 0 }}>
          {loading ? (
            <Box sx={{ padding: 2 }}>
              <TableSkeleton rows={8} columns={5} />
            </Box>
          ) : items.length === 0 ? (
            <EmptyState
              title="Nenhum item de compliance"
              description="Este contrato ainda não passou pela validação de compliance ou não há itens para auditar."
              actionLabel="Voltar"
              onAction={() => navigate(-1)}
            />
          ) : (
            <TableContainer>
              <Table size="medium">
                <TableHead>
                  <TableRow>
                    <HeaderTableCell>Item (template)</HeaderTableCell>
                    <HeaderTableCell align="center">Status IA</HeaderTableCell>
                    <HeaderTableCell align="center">Parecer do auditor</HeaderTableCell>
                    <HeaderTableCell>Observações</HeaderTableCell>
                    <HeaderTableCell align="center">Auditado em</HeaderTableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sortedItems.map((row) => {
                    const key = `${row.path}|${row.template_name}|${row.item_description}`;
                    const savingThis = saving === key;
                    const needsAuditorParecer = row.status === 'Não Compliance';
                    return (
                      <TableRow key={key} sx={{ '&:nth-of-type(odd)': { backgroundColor: '#FAFAFA' } }}>
                        <BodyTableCell>
                          <Typography variant="body2" fontWeight={600}>
                            {row.item_description}
                          </Typography>
                          {row.template_name && (
                            <Chip label={row.template_name} size="small" sx={{ mt: 0.5 }} variant="outlined" />
                          )}
                        </BodyTableCell>
                        <BodyTableCell align="center">
                          <Chip
                            size="small"
                            label={row.status || '-'}
                            color={row.status === 'Compliance' ? 'success' : 'error'}
                            variant="outlined"
                          />
                        </BodyTableCell>
                        <BodyTableCell align="center">
                          {!needsAuditorParecer ? (
                            <Typography variant="caption" color="text.secondary">
                              Não necessário
                            </Typography>
                          ) : (
                            <Box display="flex" gap={1} justifyContent="center" flexWrap="wrap" alignItems="center">
                              <Button
                                size="small"
                                variant="outlined"
                                startIcon={<CheckCircleIcon />}
                                onClick={() => handleSetAudit(row, 'Compliance')}
                                disabled={savingThis}
                                sx={getAuditButtonSx(row.auditor_status, true)}
                              >
                                OK
                              </Button>
                              <Button
                                size="small"
                                variant="outlined"
                                startIcon={<CancelIcon />}
                                onClick={() => handleSetAudit(row, 'Não Compliance')}
                                disabled={savingThis}
                                sx={getAuditButtonSx(row.auditor_status, false)}
                              >
                                NOK
                              </Button>
                            </Box>
                          )}
                        </BodyTableCell>
                        <BodyTableCell>
                          {!needsAuditorParecer ? (
                            <Typography variant="caption" color="text.secondary">—</Typography>
                          ) : (
                            <TextField
                              size="small"
                              placeholder="Observações (opcional)"
                              fullWidth
                              multiline
                              minRows={3}
                              maxRows={6}
                              value={notes[key] ?? row.auditor_notes ?? ''}
                              onChange={(e) => handleNotesChange(key, e.target.value)}
                              onBlur={() => {
                                if ((notes[key] ?? row.auditor_notes) && row.auditor_status) {
                                  handleSetAudit(row, row.auditor_status);
                                }
                              }}
                              sx={{ '& .MuiInputBase-root': { fontSize: 13, minHeight: 80 } }}
                            />
                          )}
                        </BodyTableCell>
                        <BodyTableCell align="center">
                          {!needsAuditorParecer ? (
                            <Typography variant="caption" color="text.secondary">—</Typography>
                          ) : (
                            <Typography variant="caption" color="text.secondary">
                              {row.audited_at !== '-' ? row.audited_at : '-'}
                            </Typography>
                          )}
                        </BodyTableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </StyledCard>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <MuiAlert
          onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
          severity={snackbar.severity}
          variant="filled"
          sx={{ borderRadius: '10px', fontWeight: 600 }}
        >
          {snackbar.message}
        </MuiAlert>
      </Snackbar>
    </Container>
  );
}

export default ComplianceAudit;
