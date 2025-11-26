import React from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Skeleton } from '@mui/material';
import { styled } from '@mui/system';

const StyledTableCell = styled(TableCell)(({ theme }) => ({
  fontWeight: 'bold',
  backgroundColor: theme.palette.grey[200],
  fontSize: 12,
}));

function TableSkeleton({ rows = 5, columns = 10 }) {
  return (
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            {[...Array(columns)].map((_, i) => (
              <StyledTableCell key={i}>
                <Skeleton variant="text" width="80%" />
              </StyledTableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {[...Array(rows)].map((_, rowIndex) => (
            <TableRow key={rowIndex}>
              {[...Array(columns)].map((_, colIndex) => (
                <TableCell key={colIndex}>
                  <Skeleton variant="text" width={colIndex < 3 ? "90%" : "60%"} />
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default TableSkeleton;

