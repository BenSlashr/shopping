import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { fr } from 'date-fns/locale';
import { getChartColor } from '../../lib/utils';

interface PositionData {
  date: string;
  [key: string]: string | number; // Pour les positions des différents concurrents
}

interface PositionTrendChartProps {
  data: PositionData[];
  competitors: string[];
  height?: number;
  showReferenceLine?: boolean;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="font-semibold text-gray-900 mb-2">
          {format(parseISO(label), 'PPP', { locale: fr })}
        </p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            <span className="font-medium">{entry.dataKey}:</span> #{entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const formatXAxisDate = (tickItem: string) => {
  try {
    return format(parseISO(tickItem), 'dd/MM', { locale: fr });
  } catch {
    return tickItem;
  }
};

export default function PositionTrendChart({ 
  data, 
  competitors, 
  height = 400, 
  showReferenceLine = true 
}: PositionTrendChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Aucune donnée à afficher
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart
        data={data}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis 
          dataKey="date"
          tickFormatter={formatXAxisDate}
          tick={{ fontSize: 12 }}
        />
        <YAxis 
          domain={[1, 'dataMax + 5']}
          reversed={true} // Position 1 en haut
          tick={{ fontSize: 12 }}
          label={{ value: 'Position', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        
        {/* Ligne de référence pour le top 3 */}
        {showReferenceLine && (
          <>
            <ReferenceLine y={3} stroke="#22c55e" strokeDasharray="5 5" />
            <ReferenceLine y={10} stroke="#f59e0b" strokeDasharray="5 5" />
          </>
        )}
        
        {competitors.map((competitor, index) => (
          <Line
            key={competitor}
            type="monotone"
            dataKey={competitor}
            stroke={getChartColor(index)}
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            connectNulls={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
} 