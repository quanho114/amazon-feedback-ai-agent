import { 
  PieChart, Pie, Cell, 
  BarChart, Bar, 
  LineChart, Line, 
  ScatterChart, Scatter,
  AreaChart, Area,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Treemap,
  ComposedChart,
  XAxis, YAxis, ZAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

const COLORS = ['#8b5cf6', '#ec4899', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#f97316'];

export default function ChartDisplay({ chartData }) {
  if (!chartData) return null;

  const { type, data, title, xKey, yKey, zKey, dataKey, series } = chartData;

  return (
    <div className="bg-white rounded-xl p-6 shadow-lg border border-purple-200 my-4 w-full">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
      
      <ResponsiveContainer width="100%" height={type === 'treemap' ? 500 : 400}>
        {type === 'pie' && (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              outerRadius={140}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        )}

        {type === 'bar' && (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="value" fill="#8b5cf6" />
          </BarChart>
        )}

        {type === 'line' && (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey || "name"} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey={yKey || "value"} stroke="#8b5cf6" strokeWidth={2} />
          </LineChart>
        )}

        {type === 'scatter' && (
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey || "x"} name={xKey || "X"} />
            <YAxis dataKey={yKey || "y"} name={yKey || "Y"} />
            {zKey && <ZAxis dataKey={zKey} range={[60, 400]} name={zKey} />}
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            <Legend />
            <Scatter name="Data Points" data={data} fill="#8b5cf6" />
          </ScatterChart>
        )}

        {type === 'area' && (
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey || "name"} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey={yKey || "value"} stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
          </AreaChart>
        )}

        {type === 'radar' && (
          <RadarChart data={data}>
            <PolarGrid />
            <PolarAngleAxis dataKey="name" />
            <PolarRadiusAxis />
            <Radar name="Metrics" dataKey="value" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
            <Legend />
            <Tooltip />
          </RadarChart>
        )}

        {type === 'treemap' && (
          <Treemap
            data={data}
            dataKey="value"
            stroke="#fff"
            fill="#8b5cf6"
            content={({ x, y, width, height, name, value }) => (
              <g>
                <rect
                  x={x}
                  y={y}
                  width={width}
                  height={height}
                  style={{
                    fill: COLORS[Math.floor(Math.random() * COLORS.length)],
                    stroke: '#fff',
                    strokeWidth: 2,
                  }}
                />
                {width > 50 && height > 30 && (
                  <text
                    x={x + width / 2}
                    y={y + height / 2}
                    textAnchor="middle"
                    fill="#fff"
                    fontSize={14}
                    fontWeight="bold"
                  >
                    {name}
                  </text>
                )}
                {width > 50 && height > 50 && (
                  <text
                    x={x + width / 2}
                    y={y + height / 2 + 20}
                    textAnchor="middle"
                    fill="#fff"
                    fontSize={12}
                  >
                    {value}
                  </text>
                )}
              </g>
            )}
          />
        )}

        {type === 'composed' && (
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey || "name"} />
            <YAxis />
            <Tooltip />
            <Legend />
            {series && series.map((s, idx) => {
              if (s.type === 'bar') return <Bar key={idx} dataKey={s.dataKey} fill={COLORS[idx % COLORS.length]} />;
              if (s.type === 'line') return <Line key={idx} type="monotone" dataKey={s.dataKey} stroke={COLORS[idx % COLORS.length]} />;
              if (s.type === 'area') return <Area key={idx} type="monotone" dataKey={s.dataKey} fill={COLORS[idx % COLORS.length]} fillOpacity={0.6} />;
              return null;
            })}
          </ComposedChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
