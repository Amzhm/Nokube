/**
 * Composant Input réutilisable - Design NoKube unique
 */

import { InputHTMLAttributes, forwardRef } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { useState } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helpText?: string;
  showPasswordToggle?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ 
    className = '',
    label,
    error,
    helpText,
    showPasswordToggle = false,
    type = 'text',
    ...props 
  }, ref) => {
    const [showPassword, setShowPassword] = useState(false);
    
    const inputType = showPasswordToggle 
      ? (showPassword ? 'text' : 'password')
      : type;

    const baseClasses = 'w-full px-4 py-3 border rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed';
    
    const stateClasses = error
      ? 'border-red-300 focus:border-red-500 focus:ring-red-500 bg-red-50'
      : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500 bg-white hover:border-gray-400';

    const classes = `${baseClasses} ${stateClasses} ${className}`.trim();

    return (
      <div className="space-y-1">
        {label && (
          <label className="block text-sm font-medium text-gray-700">
            {label}
          </label>
        )}
        
        <div className="relative">
          <input
            ref={ref}
            type={inputType}
            className={classes}
            {...props}
          />
          
          {showPasswordToggle && (
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-gray-700"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeOff className="w-5 h-5" />
              ) : (
                <Eye className="w-5 h-5" />
              )}
            </button>
          )}
        </div>

        {error && (
          <p className="text-sm text-red-600 mt-1">
            {error}
          </p>
        )}
        
        {helpText && !error && (
          <p className="text-sm text-gray-500 mt-1">
            {helpText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';