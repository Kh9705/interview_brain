// ── Knowledge Graph Visualization (D3.js) ───────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
  if (!API.requireAuth()) return;

  const loadingEl = document.getElementById('graph-loading');
  const emptyEl = document.getElementById('graph-empty');
  const svg = d3.select('#graph-svg');

  try {
    const data = await API.getGraph();
    const nodes = data.nodes || [];
    const edges = data.edges || [];

    loadingEl.classList.add('hidden');

    if (nodes.length === 0) {
      emptyEl.classList.remove('hidden');
      emptyEl.style.display = 'flex';
      return;
    }

    renderGraph(svg, nodes, edges);
  } catch (err) {
    loadingEl.classList.add('hidden');
    emptyEl.classList.remove('hidden');
    emptyEl.style.display = 'flex';
    console.error('Graph load error:', err);
  }
});

function renderGraph(svg, rawNodes, rawEdges) {
  const width = window.innerWidth;
  const height = window.innerHeight;

  svg.attr('viewBox', [0, 0, width, height]);

  // ── Color Scheme ─────────────────────────────────────────────────────

  const typeColors = {
    'user':    '#10b981',
    'person':  '#10b981',
    'skill':   '#06b6d4',
    'topic':   '#06b6d4',
    'company': '#7c3aed',
    'role':    '#f59e0b',
    'area':    '#ec4899',
    'default': '#64748b',
  };

  function getColor(node) {
    const type = (node.type || node.label || '').toLowerCase();
    for (const [key, color] of Object.entries(typeColors)) {
      if (type.includes(key)) return color;
    }
    return typeColors.default;
  }

  function getRadius(node) {
    const type = (node.type || node.label || '').toLowerCase();
    if (type.includes('user') || type.includes('person')) return 18;
    if (type.includes('company')) return 14;
    return 10;
  }

  // ── Prepare data ─────────────────────────────────────────────────────

  // Build node id set for filtering bad edges
  const nodeIds = new Set(rawNodes.map(n => n.id));

  const nodes = rawNodes.map(n => ({
    id: n.id,
    label: n.name || n.label || n.id,
    type: n.type || n.label || 'default',
    description: n.description || n.properties?.description || '',
    ...n,
  }));

  const links = rawEdges
    .filter(e => nodeIds.has(e.source_node_id || e.source) && nodeIds.has(e.target_node_id || e.target))
    .map(e => ({
      source: e.source_node_id || e.source,
      target: e.target_node_id || e.target,
      label: e.relationship_name || e.label || e.type || '',
    }));

  // ── Zoom ─────────────────────────────────────────────────────────────

  const g = svg.append('g');

  const zoom = d3.zoom()
    .scaleExtent([0.2, 4])
    .on('zoom', (event) => g.attr('transform', event.transform));

  svg.call(zoom);

  // Center initially
  svg.call(zoom.transform, d3.zoomIdentity.translate(width / 2, height / 2).scale(0.8));

  // ── Force Simulation ─────────────────────────────────────────────────

  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(120))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(0, 0))
    .force('collision', d3.forceCollide().radius(30));

  // ── Edges ────────────────────────────────────────────────────────────

  const link = g.append('g')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', 'rgba(255,255,255,0.08)')
    .attr('stroke-width', 1.5);

  // Edge labels
  const edgeLabel = g.append('g')
    .selectAll('text')
    .data(links)
    .join('text')
    .attr('class', 'edge-label')
    .attr('text-anchor', 'middle')
    .attr('dy', -4)
    .text(d => d.label)
    .style('opacity', 0);

  // Show edge labels on hover
  link.on('mouseenter', function(event, d) {
    d3.select(this).attr('stroke', 'rgba(255,255,255,0.3)');
    edgeLabel.filter(e => e === d).style('opacity', 1);
  }).on('mouseleave', function(event, d) {
    d3.select(this).attr('stroke', 'rgba(255,255,255,0.08)');
    edgeLabel.filter(e => e === d).style('opacity', 0);
  });

  // ── Nodes ────────────────────────────────────────────────────────────

  const node = g.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended));

  // Node circles
  node.append('circle')
    .attr('r', d => getRadius(d))
    .attr('fill', d => getColor(d))
    .attr('stroke', d => getColor(d))
    .attr('stroke-width', 2)
    .attr('fill-opacity', 0.2)
    .style('cursor', 'pointer')
    .on('mouseenter', function() {
      d3.select(this).attr('fill-opacity', 0.5).attr('stroke-width', 3);
    })
    .on('mouseleave', function() {
      d3.select(this).attr('fill-opacity', 0.2).attr('stroke-width', 2);
    });

  // Node labels
  node.append('text')
    .attr('class', 'node-label')
    .attr('dy', d => getRadius(d) + 14)
    .attr('text-anchor', 'middle')
    .text(d => truncate(d.label, 20));

  // Click to show details
  node.on('click', (event, d) => {
    const detail = document.getElementById('node-detail');
    document.getElementById('detail-title').textContent = d.label;
    document.getElementById('detail-type').innerHTML =
      `<span class="tag" style="background: ${getColor(d)}20; color: ${getColor(d)}; border-color: ${getColor(d)}40;">${d.type}</span>`;
    document.getElementById('detail-content').textContent = d.description || 'No additional details.';
    detail.classList.add('visible');
  });

  // ── Simulation Tick ──────────────────────────────────────────────────

  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);

    edgeLabel
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2);

    node.attr('transform', d => `translate(${d.x},${d.y})`);
  });

  // ── Drag Handlers ────────────────────────────────────────────────────

  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  // ── Resize ───────────────────────────────────────────────────────────

  window.addEventListener('resize', () => {
    const w = window.innerWidth;
    const h = window.innerHeight;
    svg.attr('viewBox', [0, 0, w, h]);
  });
}

function truncate(str, max) {
  if (!str) return '';
  return str.length > max ? str.slice(0, max) + '…' : str;
}
