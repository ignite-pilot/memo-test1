import type { Memo } from '../types';
import MemoItem from './MemoItem';

interface MemoListProps {
  memos: Memo[];
  onDelete: (id: number) => void;
}

export default function MemoList({ memos, onDelete }: MemoListProps) {
  if (memos.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center text-gray-500">
        작성된 메모가 없습니다.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">메모 목록</h2>
      {memos.map((memo) => (
        <MemoItem key={memo.id} memo={memo} onDelete={onDelete} />
      ))}
    </div>
  );
}

