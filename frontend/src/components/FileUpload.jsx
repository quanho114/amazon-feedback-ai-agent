import { useState } from 'react';
import { Upload, FileText, CheckCircle2, Trash2 } from 'lucide-react';
import { uploadAPI } from '../services/api';

export default function FileUpload({ onUploadSuccess }) {
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [resetting, setResetting] = useState(false);

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setProgress(20);

    try {
      setProgress(40);
      const response = await uploadAPI.uploadCSV(file);
      
      setProgress(80);
      setUploadedFile({
        name: file.name,
        rows: response.rows,
        columns: response.columns,
      });
      
      setProgress(100);
      onUploadSuccess?.(response);
      
      setTimeout(() => setProgress(0), 1000);
    } catch (error) {
      alert(`Upload failed: ${error.message}`);
      setProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset all data? This will clear uploaded data, conversation history, and vector index.')) {
      return;
    }

    setResetting(true);
    try {
      await uploadAPI.resetData();
      setUploadedFile(null);
      setProgress(0);
      onUploadSuccess?.(null); // Notify parent to update dataLoaded state
      alert('Data reset successfully! You can now upload a new file.');
    } catch (error) {
      alert(`Reset failed: ${error.message}`);
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
      <div className="flex items-center gap-3 mb-4">
        <FileText className="w-6 h-6 text-blue-600" />
        <h3 className="text-lg font-semibold">Upload CSV Data</h3>
      </div>

      <label className="block">
        <div
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
            uploading
              ? 'border-blue-400 bg-blue-50'
              : 'border-gray-300 hover:border-blue-500 hover:bg-gray-50'
          }`}
        >
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            disabled={uploading}
            className="hidden"
          />
          <Upload
            className={`w-12 h-12 mx-auto mb-3 ${
              uploading ? 'text-blue-600 animate-pulse' : 'text-gray-400'
            }`}
          />
          <p className="text-sm font-medium text-gray-700">
            {uploading ? 'Uploading...' : 'Click to select CSV file'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Supports .csv files with text and rating columns
          </p>
        </div>
      </label>

      {progress > 0 && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {uploadedFile && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-green-700">
              <CheckCircle2 className="w-5 h-5" />
              <span className="font-medium">Upload successful!</span>
            </div>
            <button
              onClick={handleReset}
              disabled={resetting}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <Trash2 className="w-4 h-4" />
              {resetting ? 'Resetting...' : 'Reset Data'}
            </button>
          </div>
          <p className="text-sm text-green-600 mt-2">
            {uploadedFile.name}
          </p>
          <p className="text-xs text-green-600">
            {uploadedFile.rows.toLocaleString()} rows •{' '}
            {uploadedFile.columns.length} columns
          </p>
        </div>
      )}
    </div>
  );
}
