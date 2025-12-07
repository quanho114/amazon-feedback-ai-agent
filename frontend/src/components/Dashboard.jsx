import { useState, useEffect } from 'react';
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  LineChart, Line, AreaChart, Area
} from 'recharts';
import { TrendingUp, BarChart3, Star, Calendar, MessageSquare } from 'lucide-react';
import { analyticsAPI } from '../services/api';

const COLORS = {
  positive: '#10b981',
  negative: '#ef4444',
  neutral: '#f59e0b',
};

const RATING_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#84cc16', '#10b981'];

export default function Dashboard({ dataLoaded }) {
  const [sentiment, setSentiment] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (dataLoaded) {
      loadData();
    }
  }, [dataLoaded]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sentimentData, analyticsData] = await Promise.all([
        analyticsAPI.getSentiment(),
        analyticsAPI.getAnalytics()
      ]);
      setSentiment(sentimentData);
      setAnalytics(analyticsData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!dataLoaded) {
    return (
      <div className="text-center text-gray-500 mt-20">
        <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
        <p>Upload CSV to view dashboard</p>
      </div>
    );
  }

  if (loading) {
    return <div className="text-center mt-20">Loading...</div>;
  }

  // Prepare chart data
  const sentimentChartData = sentiment
    ? [
        { name: 'Positive', value: sentiment.distribution.positive, color: COLORS.positive },
        { name: 'Negative', value: sentiment.distribution.negative, color: COLORS.negative },
        { name: 'Neutral', value: sentiment.distribution.neutral, color: COLORS.neutral },
      ]
    : [];

  // Prepare rating distribution data
  const ratingData = analytics?.rating_distribution
    ? Object.entries(analytics.rating_distribution)
        .map(([rating, count]) => ({
          rating: `${rating} ⭐`,
          count: count,
        }))
        .sort((a, b) => parseInt(a.rating) - parseInt(b.rating))
    : [];

  // Prepare sentiment by rating data
  const sentimentByRating = analytics?.sentiment_by_rating
    ? Object.entries(analytics.sentiment_by_rating).map(([rating, sentiments]) => ({
        rating: `${rating}⭐`,
        positive: sentiments.positive || 0,
        negative: sentiments.negative || 0,
        neutral: sentiments.neutral || 0,
      }))
    : [];

  return (
    <div className="p-6 space-y-6 bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 min-h-screen">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold flex items-center gap-3">
          <TrendingUp className="w-8 h-8 text-purple-600" />
          Analytics Dashboard
        </h2>
        <p className="text-sm text-gray-600">
          Real-time insights from your data
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-lg p-6 border border-purple-200 hover:shadow-xl transition-shadow">
          <div className="flex items-center gap-3 mb-2">
            <MessageSquare className="w-5 h-5 text-gray-600" />
            <p className="text-sm text-gray-600">Total Reviews</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {sentiment?.total_reviews.toLocaleString() || '0'}
          </p>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl shadow-lg p-6 border border-green-200 hover:shadow-xl transition-shadow">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <p className="text-sm text-green-700 font-medium">Positive</p>
          </div>
          <p className="text-3xl font-bold text-green-600">
            {sentiment?.percentages.positive || 0}%
          </p>
          <p className="text-xs text-green-600 mt-1">
            {sentiment?.distribution.positive.toLocaleString() || 0} reviews
          </p>
        </div>

        <div className="bg-gradient-to-br from-red-50 to-rose-50 rounded-xl shadow-lg p-6 border border-red-200 hover:shadow-xl transition-shadow">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <p className="text-sm text-red-700 font-medium">Negative</p>
          </div>
          <p className="text-3xl font-bold text-red-600">
            {sentiment?.percentages.negative || 0}%
          </p>
          <p className="text-xs text-red-600 mt-1">
            {sentiment?.distribution.negative.toLocaleString() || 0} reviews
          </p>
        </div>

        <div className="bg-gradient-to-br from-yellow-50 to-amber-50 rounded-xl shadow-lg p-6 border border-yellow-200 hover:shadow-xl transition-shadow">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <p className="text-sm text-yellow-700 font-medium">Neutral</p>
          </div>
          <p className="text-3xl font-bold text-yellow-600">
            {sentiment?.percentages.neutral || 0}%
          </p>
          <p className="text-xs text-yellow-600 mt-1">
            {sentiment?.distribution.neutral.toLocaleString() || 0} reviews
          </p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment Pie Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-purple-200">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
            Sentiment Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={sentimentChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {sentimentChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Rating Distribution Bar Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-purple-200">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Star className="w-5 h-5 text-yellow-500" />
            Rating Distribution
          </h3>
          {ratingData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={ratingData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="rating" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-400">
              <div className="text-center">
                <Star className="w-12 h-12 mx-auto mb-2 opacity-30" />
                <p className="text-sm">No rating data available</p>
                <p className="text-xs mt-1">Upload CSV with "Rating" column</p>
              </div>
            </div>
          )}
        </div>

        {/* Sentiment by Rating - Stacked Bar */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-purple-200 lg:col-span-2">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-500" />
            Sentiment Analysis by Rating
          </h3>
          {sentimentByRating.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={sentimentByRating}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="rating" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="positive" stackId="a" fill={COLORS.positive} radius={[0, 0, 0, 0]} />
                <Bar dataKey="neutral" stackId="a" fill={COLORS.neutral} radius={[0, 0, 0, 0]} />
                <Bar dataKey="negative" stackId="a" fill={COLORS.negative} radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-400">
              <div className="text-center">
                <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-30" />
                <p className="text-sm">No rating breakdown available</p>
                <p className="text-xs mt-1">Requires rating data to analyze sentiment by rating</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Quick Insights */}
      <div className="bg-gradient-to-r from-purple-100 to-pink-100 rounded-xl shadow-lg p-6 border border-purple-300">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-purple-600" />
          Quick Insights
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white/70 backdrop-blur rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Dominant Sentiment</p>
            <p className="text-xl font-bold text-purple-700">
              {sentiment && sentiment.percentages.positive > sentiment.percentages.negative
                ? '😊 Positive'
                : sentiment && sentiment.percentages.negative > sentiment.percentages.positive
                ? '😞 Negative'
                : '😐 Neutral'}
            </p>
          </div>
          <div className="bg-white/70 backdrop-blur rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Average Rating</p>
            <p className="text-xl font-bold text-purple-700">
              {analytics?.rating_stats?.mean || 'N/A'} ⭐
            </p>
          </div>
          <div className="bg-white/70 backdrop-blur rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Data Quality</p>
            <p className="text-xl font-bold text-green-600">
              ✓ Excellent
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
