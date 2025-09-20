import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function formatDate(date) {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(date) {
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function getMoodEmoji(mood) {
  const moodEmojis = {
    1: '😢',
    2: '😔',
    3: '😐',
    4: '😊',
    5: '😄',
  };
  return moodEmojis[mood] || '😐';
}

export function getMoodColor(mood) {
  const moodColors = {
    1: 'text-red-500',
    2: 'text-orange-500',
    3: 'text-yellow-500',
    4: 'text-green-500',
    5: 'text-blue-500',
  };
  return moodColors[mood] || 'text-gray-500';
}

export function getMoodLabel(mood) {
  const moodLabels = {
    1: 'Very Low',
    2: 'Low',
    3: 'Neutral',
    4: 'Good',
    5: 'Excellent',
  };
  return moodLabels[mood] || 'Unknown';
}

export function calculateStreak(entries) {
  if (!entries || entries.length === 0) return 0;
  
  const sortedEntries = entries.sort((a, b) => new Date(b.date) - new Date(a.date));
  let streak = 0;
  let currentDate = new Date();
  
  for (const entry of sortedEntries) {
    const entryDate = new Date(entry.date);
    const daysDiff = Math.floor((currentDate - entryDate) / (1000 * 60 * 60 * 24));
    
    if (daysDiff === streak) {
      streak++;
      currentDate = entryDate;
    } else {
      break;
    }
  }
  
  return streak;
}

export function generateRandomAlias() {
  const adjectives = [
    'Blue', 'Green', 'Red', 'Purple', 'Golden', 'Silver', 'Bright', 'Dark',
    'Swift', 'Gentle', 'Brave', 'Kind', 'Wise', 'Calm', 'Strong', 'Peaceful',
    'Serene', 'Hopeful', 'Radiant', 'Luminous', 'Tranquil', 'Harmonious'
  ];
  const nouns = [
    'Phoenix', 'Dragon', 'Eagle', 'Wolf', 'Bear', 'Lion', 'Tiger', 'Fox',
    'Owl', 'Dove', 'Butterfly', 'Star', 'Moon', 'Sun', 'Ocean', 'Mountain',
    'River', 'Forest', 'Garden', 'Flower', 'Tree', 'Cloud'
  ];
  
  const adjective = adjectives[Math.floor(Math.random() * adjectives.length)];
  const noun = nouns[Math.floor(Math.random() * nouns.length)];
  const number = Math.floor(Math.random() * 900) + 100;
  
  return `${adjective}${noun}${number}`;
}

export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

export function throttle(func, limit) {
  let inThrottle;
  return function() {
    const args = arguments;
    const context = this;
    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}
