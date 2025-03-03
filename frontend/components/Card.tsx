import React, { ReactNode } from 'react';
import styled from 'styled-components';

interface CardProps {
  children: ReactNode;
  className?: string;
}

const Card = ({ children, className }: CardProps) => {
  return (
    <StyledWrapper className={className}>
      <div className="card">
        <div className="card-content">
          {children}
        </div>
      </div>
    </StyledWrapper>
  );
}

const StyledWrapper = styled.div`
  .card {
    background-image: linear-gradient(163deg, #5C8DF6 0%, #145af2 100%);
    border-radius: 16px;
    transition: all 0.3s;
    padding: 2px;
    width: 100%; /* Full width for form integration */
  }

  .card-content {
    width: 100%;
    height: 100%;
    background-color: #ffffff;
    border-radius: 14px;
    transition: all 0.2s;
    padding: 1.5rem;
    box-sizing: border-box;
    color: #1a1a1a;
  }

  /* More subtle hover effects for form cards */
  .card:hover {
    box-shadow: 0px 4px 20px rgba(92, 141, 246, 0.3);
    transform: translateY(-2px);
  }

  @media (max-width: 768px) {
    .card {
      width: 100%;
    }
    
    .card-content {
      padding: 1rem;
    }
  }
`;

export default Card;