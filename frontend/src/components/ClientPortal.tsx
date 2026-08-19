'use client';

import { ReactNode, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

interface ClientPortalProps {
  children: ReactNode;
  selector?: string;
}

export function ClientPortal({ children, selector }: ClientPortalProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  const container = selector ? document.querySelector(selector) : document.body;
  return container ? createPortal(children, container) : null;
}
