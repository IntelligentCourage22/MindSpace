import React, { createContext, useContext } from 'react';

const ToastContext = createContext();

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export const toast = ({ title, description, variant = "default" }) => {
  // Simple toast function - will be handled by the context
  return { title, description, variant };
};
