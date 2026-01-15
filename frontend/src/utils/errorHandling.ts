/**
 * Error handling utilities for API responses.
 *
 * Converts API errors to user-friendly messages.
 */

import { AxiosError } from 'axios';

/**
 * API error response shape from backend.
 */
interface ApiErrorResponse {
  error: string;
  status: number;
  details?: Record<string, unknown>;
}

/**
 * Parsed error with user-friendly message.
 */
export interface ParsedError {
  message: string;
  status: number;
  isNetworkError: boolean;
  isAuthError: boolean;
  isValidationError: boolean;
  field?: string;
}

/**
 * User-friendly error messages by status code.
 */
const STATUS_MESSAGES: Record<number, string> = {
  400: 'Invalid request. Please check your input.',
  401: 'Authentication required. Please log in.',
  403: 'Access denied. You do not have permission.',
  404: 'Resource not found.',
  409: 'Conflict. This resource may already exist.',
  422: 'Validation error. Please check your input.',
  429: 'Too many requests. Please wait a moment and try again.',
  500: 'Server error. Please try again later.',
  502: 'Service temporarily unavailable. Please try again later.',
  503: 'Service temporarily unavailable. Please try again later.',
};

/**
 * Parse an Axios error into a user-friendly format.
 */
export function parseApiError(error: unknown): ParsedError {
  // Network error (no response)
  if (error instanceof AxiosError && !error.response) {
    return {
      message: 'Unable to connect to server. Please check your connection.',
      status: 0,
      isNetworkError: true,
      isAuthError: false,
      isValidationError: false,
    };
  }

  // Axios error with response
  if (error instanceof AxiosError && error.response) {
    const { status, data } = error.response;
    const apiError = data as ApiErrorResponse | undefined;

    // Use API error message if available, otherwise use status message
    const message =
      apiError?.error ||
      STATUS_MESSAGES[status] ||
      `Request failed with status ${status}`;

    return {
      message,
      status,
      isNetworkError: false,
      isAuthError: status === 401 || status === 403,
      isValidationError: status === 400 || status === 422,
      field: apiError?.details?.field as string | undefined,
    };
  }

  // Unknown error
  if (error instanceof Error) {
    return {
      message: error.message || 'An unexpected error occurred.',
      status: 0,
      isNetworkError: false,
      isAuthError: false,
      isValidationError: false,
    };
  }

  // Fallback
  return {
    message: 'An unexpected error occurred.',
    status: 0,
    isNetworkError: false,
    isAuthError: false,
    isValidationError: false,
  };
}

/**
 * Get a user-friendly error message from any error.
 */
export function getErrorMessage(error: unknown): string {
  return parseApiError(error).message;
}

/**
 * Check if error is an authentication error.
 */
export function isAuthError(error: unknown): boolean {
  return parseApiError(error).isAuthError;
}

/**
 * Check if error is a network error.
 */
export function isNetworkError(error: unknown): boolean {
  return parseApiError(error).isNetworkError;
}
