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
  Area,
  AreaChart
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { fr } from 'date-fns/locale';
import { getChartColor } from '../../lib/utils';

interface ShareOfVoiceTrendData {
  date: string;
  [key: string]: string | number; // Pour les share of voice des différents concurrents
}

interface ShareOfVoiceTrendChartProps {
  data: ShareOfVoiceTrendData[];
  competitors: string[];
  type?: 'line' | 'area';
  height?: number;
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
            <span className="font-medium">{entry.dataKey}:</span> {entry.value.toFixed(1)}%
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

const formatYAxisPercentage = (value: number) => {
  return `${value}%`;
};

export default function ShareOfVoiceTrendChart({ 
  data, 
  competitors, 
  type = 'line',
  height = 400 
}: ShareOfVoiceTrendChartProps) {
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
            domain={[0, 100]}
            tickFormatter={formatYAxisPercentage}
            tick={{ fontSize: 12 }}
            label={{ value: 'Share of Voice (%)', angle: -90, position: 'insideLeft' }}
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
              fillOpacity={0.6}
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
          domain={[0, 'dataMax + 5']}
          tickFormatter={formatYAxisPercentage}
          tick={{ fontSize: 12 }}
          label={{ value: 'Share of Voice (%)', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        
        {competitors.map((competitor, index) => (
          <Line
            key={competitor}
            type="monotone"
            dataKey={competitor}
            stroke={getChartColor(index)}
            strokeWidth={3}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            connectNulls={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
} 