import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { ChartDataPoint } from '../types';
// Import the Card component
import Card from './Card';

interface DataChartProps {
  data: ChartDataPoint[];
  title: string;
  dataKey: string;
  unit: string;
  color: string;
}

// Performance optimization: Memoize DataChart to prevent redundant Recharts SVG re-renders
// when parent state updates.
const DataChart: React.FC<DataChartProps> = React.memo(({ data, title, dataKey, unit, color }) => {
  return (
    <Card title={title}>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#4a4a4a" />
          <XAxis dataKey="name" stroke="#a0a0a0" />
          <YAxis stroke="#a0a0a0" unit={unit} />
          <Tooltip
            contentStyle={{ backgroundColor: '#2a2a2a', border: 'none', borderRadius: '5px' }}
            labelStyle={{ color: '#e0e0e0' }}
            itemStyle={{ color: color }}
          />
          <Line
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            strokeWidth={2}
            dot={{ r: 3, strokeWidth: 1 }}
            activeDot={{ r: 6, stroke: color, strokeWidth: 2, fill: '#fff' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
});

export default DataChart;