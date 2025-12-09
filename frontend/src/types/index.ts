export interface Memo {
  id: number;
  title: string;
  content: string | null;
  created_at: string;
  updated_at: string;
}

export interface MemoCreate {
  title: string;
  content?: string | null;
}

