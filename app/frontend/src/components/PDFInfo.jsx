import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { 
  Card, CardContent, Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Box, Typography, Chip, Container
} from '@mui/material';
import { styled, keyframes } from '@mui/system';
import BusinessIcon from '@mui/icons-material/Business';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import api from "../utils/api";
import TableSkeleton from "./TableSkeleton";
import EmptyState from "./EmptyState";

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

const StyledTableCell = styled(TableCell)(({ theme }) => ({
  fontWeight: 700,
  backgroundColor: '#1B3139',
  color: 'white',
  fontSize: 13,
  padding: '16px',
  textAlign: 'center',
}));

const StyledTableRow = styled(TableRow)(({ theme }) => ({
  transition: 'all 0.2s ease',
  '&:hover': {
    backgroundColor: '#FFF8F6',
    transform: 'scale(1.01)',
  },
  '&:nth-of-type(odd)': {
    backgroundColor: '#FAFAFA',
  }
}));

const StyledTableCell2 = styled(TableCell)(({ theme }) => ({
  fontSize: 13,
  color: '#555',
  padding: '16px',
  textAlign: 'center',
  fontWeight: 600,
}));

const HeaderBox = styled(Box)(({ theme }) => ({
  background: 'linear-gradient(135deg, #FF3621 0%, #E02F1A 100%)',
  padding: '32px',
  borderRadius: '16px',
  marginBottom: '24px',
  color: 'white',
  boxShadow: '0 8px 24px rgba(255,54,33,0.3)',
  animation: `${fadeIn} 0.8s ease-out`,
}));

function PDFInfo() {
  const { pdf } = useParams();
  const [pdfData, setPdfData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.get("/api/all_data", {
          params: { pdf: pdf }
        });
        setPdfData(response.data);
      } catch (error) {
        console.error('Error fetching data:', error);
        setPdfData([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [pdf]);

  const formatValue = (value) => {
    if (!value || value === '-') return '-';
    return value;
  };

  return (
    <Container sx={{ marginTop: 12, maxWidth: '1400px !important' }}>
      <HeaderBox>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={2}>
            <BusinessIcon sx={{ fontSize: 48 }} />
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 800, marginBottom: 0.5 }}>
                Detalhes do Contrato
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                {pdf}
              </Typography>
            </Box>
          </Box>
          <Chip 
            icon={<TrendingUpIcon style={{ color: 'white' }} />}
            label="Contrato Analisado" 
            sx={{ 
              backgroundColor: 'rgba(255,255,255,0.2)', 
              color: 'white',
              fontWeight: 600,
              border: '1px solid rgba(255,255,255,0.3)',
              fontSize: 13
            }} 
          />
        </Box>
      </HeaderBox>

      <StyledCard>
        <CardContent sx={{ padding: 0 }}>
          {loading ? (
            <Box sx={{ padding: 2 }}>
              <TableSkeleton rows={3} columns={16} />
            </Box>
          ) : pdfData.length === 0 ? (
            <EmptyState
              title="Nenhum dado encontrado"
              description="Os dados do contrato ainda não foram extraídos deste PDF"
            />
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <StyledTableCell>Tipo</StyledTableCell>
                    <StyledTableCell>Nome</StyledTableCell>
                    <StyledTableCell>Contratante</StyledTableCell>
                    <StyledTableCell>Contratado</StyledTableCell>
                    <StyledTableCell>Valor Total</StyledTableCell>
                    <StyledTableCell>Moeda</StyledTableCell>
                    <StyledTableCell>Assinatura</StyledTableCell>
                    <StyledTableCell>Início</StyledTableCell>
                    <StyledTableCell>Fim</StyledTableCell>
                    <StyledTableCell>Prazo</StyledTableCell>
                    <StyledTableCell>Pagamento</StyledTableCell>
                    <StyledTableCell>Multa</StyledTableCell>
                    <StyledTableCell>Foro</StyledTableCell>
                  </TableRow>
                </TableHead>

                <TableBody>
                  {pdfData.map((data, index) => (
                    <StyledTableRow key={index}>
                      <StyledTableCell2>
                        <Chip label={data.tipo_contrato || '-'} size="small" color="primary" sx={{ fontWeight: 600 }} />
                      </StyledTableCell2>
                      <StyledTableCell2>{formatValue(data.nome_contrato)}</StyledTableCell2>
                      <StyledTableCell2>
                        <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
                          <BusinessIcon sx={{ fontSize: 18, color: '#FF3621' }} />
                          <span>{data.contratante || '-'}</span>
                        </Box>
                      </StyledTableCell2>
                      <StyledTableCell2>
                        <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
                          <BusinessIcon sx={{ fontSize: 18, color: '#1976D2' }} />
                          <span>{data.contratado || '-'}</span>
                        </Box>
                      </StyledTableCell2>
                      <StyledTableCell2 sx={{ color: '#FF3621', fontWeight: 700 }}>
                        {formatValue(data.valor_total)}
                      </StyledTableCell2>
                      <StyledTableCell2>
                        <Chip label={data.moeda || '-'} size="small" variant="outlined" />
                      </StyledTableCell2>
                      <StyledTableCell2>{formatValue(data.data_assinatura)}</StyledTableCell2>
                      <StyledTableCell2>{formatValue(data.data_inicio_vigencia)}</StyledTableCell2>
                      <StyledTableCell2>{formatValue(data.data_fim_vigencia)}</StyledTableCell2>
                      <StyledTableCell2>
                        <Chip label={data.prazo_vigencia || '-'} size="small" sx={{ fontWeight: 600 }} />
                      </StyledTableCell2>
                      <StyledTableCell2>{formatValue(data.forma_pagamento)}</StyledTableCell2>
                      <StyledTableCell2 sx={{ color: '#d32f2f', fontWeight: 700 }}>
                        {formatValue(data.multa_rescisao)}
                      </StyledTableCell2>
                      <StyledTableCell2>{formatValue(data.foro)}</StyledTableCell2>
                    </StyledTableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </StyledCard>
    </Container>
  );
}

export default PDFInfo;
