import type { Memo } from '../types';

interface MemoItemProps {
  memo: Memo;
  onDelete: (id: number) => void;
}

export default function MemoItem({ memo, onDelete }: MemoItemProps) {
  const handleDelete = () => {
    if (window.confirm('정말 이 메모를 삭제하시겠습니까?')) {
      onDelete(memo.id);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold text-gray-900">{memo.title}</h3>
        <button
          onClick={handleDelete}
          className="text-red-600 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 rounded px-2 py-1 transition-colors"
          aria-label="메모 삭제"
        >
          삭제
        </button>
      </div>
      {memo.content && (
        <p className="text-gray-700 mb-3 whitespace-pre-wrap">{memo.content}</p>
      )}
      <p className="text-sm text-gray-500">
        작성일: {formatDate(memo.created_at)}
      </p>
    </div>
  );
}

