import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import MemoForm from '../MemoForm';

describe('MemoForm', () => {
  it('renders form fields', () => {
    const onCreate = vi.fn();
    render(<MemoForm onCreate={onCreate} />);
    
    expect(screen.getByLabelText(/제목/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/내용/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /메모 작성/i })).toBeInTheDocument();
  });

  it('calls onCreate with memo data on submit', () => {
    const onCreate = vi.fn();
    render(<MemoForm onCreate={onCreate} />);
    
    const titleInput = screen.getByLabelText(/제목/i);
    const contentInput = screen.getByLabelText(/내용/i);
    const submitButton = screen.getByRole('button', { name: /메모 작성/i });
    
    fireEvent.change(titleInput, { target: { value: 'Test Title' } });
    fireEvent.change(contentInput, { target: { value: 'Test Content' } });
    fireEvent.click(submitButton);
    
    expect(onCreate).toHaveBeenCalledWith({
      title: 'Test Title',
      content: 'Test Content',
    });
  });

  it('clears form after submit', () => {
    const onCreate = vi.fn();
    render(<MemoForm onCreate={onCreate} />);
    
    const titleInput = screen.getByLabelText(/제목/i) as HTMLInputElement;
    const submitButton = screen.getByRole('button', { name: /메모 작성/i });
    
    fireEvent.change(titleInput, { target: { value: 'Test Title' } });
    fireEvent.click(submitButton);
    
    expect(titleInput.value).toBe('');
  });
});

