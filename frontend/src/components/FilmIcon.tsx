import React from "react";

interface FilmIconProps {
  className?: string;
  size?: number;
}

export const FilmIcon: React.FC<FilmIconProps> = ({ 
  className = "", 
  size = 24 
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {/* Film strip with sprocket holes */}
      <rect x="2" y="3" width="20" height="18" rx="2" ry="2" />
      <circle cx="8" cy="7" r="1" />
      <circle cx="8" cy="12" r="1" />
      <circle cx="8" cy="17" r="1" />
      <circle cx="16" cy="7" r="1" />
      <circle cx="16" cy="12" r="1" />
      <circle cx="16" cy="17" r="1" />
      <line x1="2" y1="9" x2="22" y2="9" />
      <line x1="2" y1="15" x2="22" y2="15" />
    </svg>
  );
};

export default FilmIcon;
