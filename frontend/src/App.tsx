import { useState, useEffect } from 'react';
import { memoService } from './services/api';
import type { Memo, MemoCreate } from './types';
import MemoList from './components/MemoList';
import MemoForm from './components/MemoForm';

function App() {
  const [memos, setMemos] = useState<Memo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMemos = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await memoService.getMemos();
      setMemos(data);
    } catch (err) {
      setError('메모를 불러오는데 실패했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMemos();
  }, []);

  const handleCreateMemo = async (memo: MemoCreate) => {
    try {
      await memoService.createMemo(memo);
      await loadMemos();
    } catch (err) {
      setError('메모를 생성하는데 실패했습니다.');
      console.error(err);
    }
  };

  const handleDeleteMemo = async (id: number) => {
    try {
      await memoService.deleteMemo(id);
      await loadMemos();
    } catch (err) {
      setError('메모를 삭제하는데 실패했습니다.');
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
          메모 앱
        </h1>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <MemoForm onCreate={handleCreateMemo} />

        {loading ? (
          <div className="text-center py-8 text-gray-600">로딩 중...</div>
        ) : (
          <MemoList memos={memos} onDelete={handleDeleteMemo} />
        )}
      </div>
    </div>
  );
}

export default App;

