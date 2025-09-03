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
  AreaChart,
  Area
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { fr } from 'date-fns/locale';
import { getChartColor } from '../../lib/utils';

interface PriceData {
  date: string;
  [key: string]: string | number; // Pour les prix des différents concurrents
}

interface PriceChartProps {
  data: PriceData[];
  competitors: string[];
  currency?: string;
  type?: 'line' | 'area';
  height?: number;
}

const formatCurrency = (value: number, currency: string = 'EUR') => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="font-semibold text-gray-900 mb-2">
          {format(parseISO(label), 'PPP', { locale: fr })}
        </p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            <span className="font-medium">{entry.dataKey}:</span> {formatCurrency(entry.value)}
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

const formatYAxisPrice = (value: number) => {
  return formatCurrency(value);
};

export default function PriceChart({ 
  data, 
  competitors, 
  currency = 'EUR',
  type = 'line',
  height = 400 
}: PriceChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Aucune donnée à afficher
      </div>
    );
  }

  if (type === 'area') {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart
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
            tickFormatter={formatYAxisPrice}
            tick={{ fontSize: 12 }}
            label={{ value: `Prix (${currency})`, angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          
          {competitors.map((competitor, index) => (
            <Area
              key={competitor}
              type="monotone"
              dataKey={competitor}
              stackId="1"
              stroke={getChartColor(index)}
              fill={getChartColor(index)}
              fillOpacity={0.3}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
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
          tickFormatter={formatYAxisPrice}
          tick={{ fontSize: 12 }}
          label={{ value: `Prix (${currency})`, angle: -90, position: 'insideLeft' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        
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