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
        <div className="card2">
          {children}
        </div>
      </div>
    </StyledWrapper>
  );
}

const StyledWrapper = styled.div`
  .card {
    width: 190px;
    height: 254px;
    background-image: linear-gradient(163deg, #00ff75 0%, #3700ff 100%);
    border-radius: 20px;
    transition: all 0.3s;
    padding: 2px; /* Add padding for the gradient border effect */
  }

  .card2 {
    width: 100%;
    height: 100%;
    background-color: #1a1a1a;
    border-radius: 18px; /* Slightly smaller than card radius */
    transition: all 0.2s;
    padding: 20px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: white;
  }

  .card2:hover {
    transform: scale(0.98);
  }

  .card:hover {
    box-shadow: 0px 0px 30px 1px rgba(0, 255, 117, 0.30);
  }

  /* Add responsive behavior */
  @media (max-width: 768px) {
    .card {
      width: 160px;
      height: 220px;
    }
  }
`;

export default Card;