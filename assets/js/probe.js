// On-device readout (?probe): Mobile Safari hands no terminal its numbers, so the page prints its
// own viewport measurements into a fixed layer and the screenshot is the measurement.
export default function probe() {
  const p = document.createElement('div');
  p.style.cssText = 'position:fixed;inset-block-start:0;inset-inline:0;z-index:99999;'
    + 'font:12px/1.35 ui-monospace,monospace;background:#000;color:#0f0;padding:4px 6px;white-space:pre';
  const unit = (u) => {
    const d = document.createElement('div');
    d.style.cssText = 'position:absolute;top:0;left:0;width:1px;height:100' + u + ';visibility:hidden';
    document.body.appendChild(d);
    const h = d.getBoundingClientRect().height;
    d.remove();
    return Math.round(h);
  };
  const paint = () => {
    const bar = document.querySelector('.bar');
    const r = bar ? bar.getBoundingClientRect() : { top: -1, bottom: -1, height: -1 };
    const vv = window.visualViewport || { height: -1 };
    p.textContent = [
      'inner ' + innerHeight + '  visual ' + Math.round(vv.height) + '  lvh ' + unit('lvh') + ' svh ' + unit('svh') + ' dvh ' + unit('dvh'),
      'bar top ' + Math.round(r.top) + ' bottom ' + Math.round(r.bottom) + ' h ' + Math.round(r.height) + '  gap ' + Math.round(innerHeight - r.bottom),
      'scrollY ' + Math.round(scrollY) + '  docH ' + document.documentElement.scrollHeight,
    ].join('\n');
  };
  document.body.appendChild(p);
  paint();
  addEventListener('scroll', paint, { passive: true });
  addEventListener('resize', paint);
  if (window.visualViewport) visualViewport.addEventListener('resize', paint);
}
